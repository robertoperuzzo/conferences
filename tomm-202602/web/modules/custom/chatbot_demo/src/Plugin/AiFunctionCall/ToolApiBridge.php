<?php

namespace Drupal\chatbot_demo\Plugin\AiFunctionCall;

use Drupal\ai\Attribute\FunctionCall;
use Drupal\ai\Base\FunctionCallBase;
use Drupal\ai\Exception\AiToolsValidationException;
use Drupal\ai\PluginManager\AiDataTypeConverterPluginManager;
use Drupal\ai\Service\FunctionCalling\StructuredExecutableFunctionCallInterface;
use Drupal\ai\Service\FunctionCalling\FunctionCallInterface;
use Drupal\ai\Utility\ContextDefinitionNormalizer;
use Drupal\chatbot_demo\Plugin\AiFunctionCall\Derivative\ToolApiBridgeDeriver;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\tool\Tool\ToolManager;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Bridges Tool API plugins to FunctionCall API.
 *
 * This plugin acts as a wrapper that allows the AI module to use any
 * plugin that implements Drupal's Tool API, even though the AI module
 * doesn't natively support Tool API yet.
 */
#[FunctionCall(
  id: 'tool_api_bridge',
  function_name: 'tool_api_bridge',
  name: new TranslatableMarkup('Tool API Bridge'),
  description: 'Executes Tool API plugins as AI function calls',
  deriver: ToolApiBridgeDeriver::class
)]
class ToolApiBridge extends FunctionCallBase implements StructuredExecutableFunctionCallInterface {

  /**
   * Constructs a ToolApiBridge plugin.
   *
   * @param array<string, mixed> $configuration
   *   A configuration array containing information about the plugin instance.
   * @param string $plugin_id
   *   The plugin_id for the plugin instance.
   * @param mixed $plugin_definition
   *   The plugin implementation definition.
   * @param \Drupal\ai\Utility\ContextDefinitionNormalizer $context_definition_normalizer
   *   The context definition normalizer service.
   * @param \Drupal\ai\PluginManager\AiDataTypeConverterPluginManager $data_type_converter_manager
   *   The ai data type converter plugin manager.
   * @param \Drupal\tool\Tool\ToolManager $toolManager
   *   The tool plugin manager.
   * @param \Drupal\Core\Session\AccountInterface $currentUser
   *   The current user service.
   */
  public function __construct(
    array $configuration,
    $plugin_id,
    $plugin_definition,
    ContextDefinitionNormalizer $context_definition_normalizer,
    AiDataTypeConverterPluginManager $data_type_converter_manager,
    protected ToolManager $toolManager,
    protected AccountInterface $currentUser,
  ) {
    parent::__construct(
      $configuration,
      $plugin_id,
      $plugin_definition,
      $context_definition_normalizer,
      $data_type_converter_manager
    );
  }

  /**
   * {@inheritdoc}
   */
  public static function create(
    ContainerInterface $container,
    array $configuration,
    $plugin_id,
    $plugin_definition
  ): FunctionCallInterface|static {
    return new static(
      $configuration,
      $plugin_id,
      $plugin_definition,
      $container->get('ai.context_definition_normalizer'),
      $container->get('plugin.manager.ai_data_type_converter'),
      $container->get('plugin.manager.tool'),
      $container->get('current_user'),
    );
  }

  /**
   * {@inheritdoc}
   */
  public function execute(): void {
    // Initialize output.
    $this->stringOutput = '';

    // Get the Tool plugin ID from the derivative.
    $derivative_id = $this->getDerivativeId();
    if (!$derivative_id) {
      throw new AiToolsValidationException('Tool API bridge derivative ID is missing.');
    }

    $tool_plugin_id = $this->pluginDefinition['tool_plugin_id'] ?? $derivative_id;

    // Add logging to debug which tool is being called.
    \Drupal::logger('chatbot_demo')->debug('ToolApiBridge executing: @id (derivative: @derivative)', [
      '@id' => $tool_plugin_id,
      '@derivative' => $derivative_id,
    ]);

    try {
      // Create an instance of the Tool API plugin.
      $tool = $this->toolManager->createInstance($tool_plugin_id);

      // Get input definitions from the tool.
      $input_definitions = $tool->getInputDefinitions();

      // Map FunctionCall context values to Tool API input values FIRST
      // (before access check, as access might validate inputs).
      $missing_required = [];
      $provided_values = [];
      
      foreach ($input_definitions as $key => $input_def) {
        $value = NULL;
        
        // Try to get the context value - may not exist if context wasn't defined.
        try {
          $value = $this->getContextValue($key);
          $provided_values[$key] = $value;
        }
        catch (\Exception $e) {
          // Context doesn't exist, use default if available.
          $value = $input_def->getDefaultValue();
        }

        // Convert string JSON to array if needed.
        if (is_string($value) && !empty($value) && substr($value, 0, 1) === "{" && json_decode($value, TRUE) !== NULL) {
          $value = json_decode($value, TRUE);
        }

        // Track missing required values for better error messages.
        if ($input_def->isRequired() && ($value === NULL || $value === '')) {
          $missing_required[] = sprintf(
            '%s (%s)',
            $key,
            $input_def->getLabel()
          );
        }

        // Set the input value on the tool (before access check!).
        $tool->setInputValue($key, $value);
      }

      // Now check access AFTER setting input values.
      if (!$tool->access($this->currentUser)) {
        throw new AiToolsValidationException('Access denied to tool: ' . $tool_plugin_id);
      }

      // Provide helpful error if required values are missing.
      if (!empty($missing_required)) {
        $provided_info = !empty($provided_values) 
          ? ' Provided: ' . implode(', ', array_keys($provided_values)) 
          : ' No values were provided.';
        
        throw new AiToolsValidationException(
          sprintf(
            'Tool "%s" requires: %s.%s',
            $tool_plugin_id,
            implode(', ', $missing_required),
            $provided_info
          )
        );
      }

      // Execute the tool - this always returns $this, check result after.
      $tool->execute();

      // Get the result.
      $result = $tool->getResult();

      if (!$result->isSuccess()) {
        $error_msg = (string) $result->getMessage();
        
        // Provide helpful context for MCP-specific errors.
        if (strpos($tool_plugin_id, 'mcp_tool:') === 0) {
          $parts = explode(':', $tool_plugin_id);
          if (count($parts) >= 3) {
            $server_id = $parts[1];
            $tool_name = $parts[2];
            throw new AiToolsValidationException(
              sprintf(
                'MCP Tool "%s" on server "%s" failed: %s. Please check that the tool is enabled in the MCP server configuration.',
                $tool_name,
                $server_id,
                $error_msg
              )
            );
          }
        }
        
        // Extract parameter names from validation error if possible.
        if (preg_match_all('/Input (\w+):/', $error_msg, $matches)) {
          $failed_params = array_unique($matches[1]);
          
          // Build detailed error with what we provided.
          $details = [];
          foreach ($failed_params as $param) {
            $provided = isset($provided_values[$param]) ? $provided_values[$param] : 'NOT PROVIDED';
            $details[] = sprintf('%s = %s', $param, is_scalar($provided) ? var_export($provided, TRUE) : gettype($provided));
          }
          
          throw new AiToolsValidationException(
            sprintf(
              'Tool "%s" validation failed. Required parameters: %s. Values: %s',
              $tool_plugin_id,
              implode(', ', $failed_params),
              implode(', ', $details)
            )
          );
        }
        
        throw new AiToolsValidationException(
          sprintf('Tool "%s" execution failed: %s', $tool_plugin_id, $error_msg)
        );
      }

      // Capture structured output (context_values) from the Tool API result.
      $context_values = $result->getContextValues();
      if (!empty($context_values)) {
        $this->structuredOutput = $context_values;
      }

      // Build the string output: start with the tool's message.
      $this->stringOutput = (string) $result->getMessage();
      
      // Enhance the output with formatted structured data as JSON for better readability.
      if (!empty($context_values)) {
        $formatted_json = $this->formatStructuredOutputAsJson($context_values);
        if (!empty($formatted_json)) {
          $this->stringOutput .= "\n\n" . $formatted_json;
        }
      }
    }
    catch (AiToolsValidationException $e) {
      // Re-throw our own exceptions.
      throw $e;
    }
    catch (\Exception $e) {
      throw new AiToolsValidationException('Tool API bridge execution failed: ' . $e->getMessage());
    }
  }

  /**
   * Format structured output data as JSON.
   *
   * Converts structured data from tool execution results into pretty-printed
   * JSON format for display to users and AI agents.
   *
   * @param array<string, mixed> $data
   *   The structured output data to format.
   *
   * @return string
   *   JSON representation of the data.
   */
  protected function formatStructuredOutputAsJson(array $data): string {
    try {
      $json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
      if ($json === FALSE) {
        return 'Error encoding structured output as JSON.';
      }
      return "Structured output:\n```json\n" . $json . "\n```";
    }
    catch (\Exception $e) {
      return 'Error formatting structured output: ' . $e->getMessage();
    }
  }

  /**
   * {@inheritdoc}
   *
   * Returns structured output containing the Tool API's context values
   * as defined by the tool's output_definitions.
   *
   * The structure matches the output_definitions from the Tool API plugin,
   * for example:
   * - GetCollections tool returns: ['collections' => [...]]
   * - AddToCart tool returns: ['order_item_id' => 123]
   *
   * @return array<string, mixed>
   *   The structured output data matching the tool's output_definitions.
   */
  public function getStructuredOutput(): array {
    return $this->structuredOutput;
  }

  /**
   * {@inheritdoc}
   *
   * Sets structured output data from a provided array.
   *
   * The structure should match the output_definitions from the Tool API plugin.
   *
   * @param array<array-key, mixed> $output
   *   The structured output data containing the tool's output values.
   */
  public function setStructuredOutput(array $output): void {
    $this->structuredOutput = $output;
  }

}
