<?php

namespace Drupal\chatbot_demo\Plugin\AiFunctionCall\Derivative;

use Drupal\Component\Plugin\Derivative\DeriverBase;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Plugin\Discovery\ContainerDeriverInterface;
use Drupal\Core\StringTranslation\StringTranslationTrait;
use Drupal\tool\Tool\ToolManager;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Derives FunctionCall plugins from Tool API plugins.
 *
 * This bridges the gap between Drupal's Tool API and the AI module's
 * FunctionCall API, automatically exposing all Tool API plugins as
 * AI function calls.
 */
class ToolApiBridgeDeriver extends DeriverBase implements ContainerDeriverInterface {

  use StringTranslationTrait;

  /**
   * Constructs a new ToolApiBridgeDeriver object.
   *
   * @param \Drupal\tool\Tool\ToolManager $toolManager
   *   The tool plugin manager.
   */
  public function __construct(
    protected ToolManager $toolManager,
  ) {
  }

  /**
   * {@inheritdoc}
   */
  public static function create(ContainerInterface $container, $base_plugin_id) {
    return new static(
      $container->get('plugin.manager.tool'),
    );
  }

  /**
   * {@inheritdoc}
   *
   * @param array<string, mixed> $base_plugin_definition
   *   The base plugin definition.
   *
   * @return array<string, mixed>
   *   The derivative definitions.
   */
  public function getDerivativeDefinitions($base_plugin_definition): array {
    if (empty($this->derivatives)) {
      $definitions = [];

      // Get all Tool API plugin definitions.
      $tool_definitions = $this->toolManager->getDefinitions();

      foreach ($tool_definitions as $tool_id => $tool_definition) {
        // Create a derivative for each Tool API plugin.
        $definition = $base_plugin_definition;
        $definition['id'] = 'tool_api_bridge:' . $tool_id;
        $definition['name'] = $tool_definition->getLabel() ?? $tool_id;
        $definition['group'] = 'tool_api';
        $definition['function_name'] = str_replace(':', '__', $definition['id']);
        $definition['description'] = $tool_definition->getDescription() ?? '';
        $definition['tool_plugin_id'] = $tool_id;

        // Convert Tool API input definitions to FunctionCall context definitions.
        $context_definitions = [];
        $input_definitions = $tool_definition->getInputDefinitions();
        if (!empty($input_definitions)) {
          foreach ($input_definitions as $key => $input_def) {
            // Map Tool API types to FunctionCall types.
            $type = $this->mapToolTypeToContextType($input_def->getDataType());
            $is_required = $input_def->isRequired();
            $description = $input_def->getDescription() ?? '';
            $default_value = $input_def->getDefaultValue();

            $context_definitions[$key] = new ContextDefinition(
              $type,
              $input_def->getLabel(),
              $is_required,
              FALSE,
              $description,
              $default_value,
              [],
            );
          }
        }

        $definition['context_definitions'] = $context_definitions;

        // Convert Tool API output definitions to FunctionCall output definitions.
        $output_definitions = [];
        $tool_output_definitions = $tool_definition->getOutputDefinitions();
        if (!empty($tool_output_definitions)) {
          foreach ($tool_output_definitions as $key => $output_def) {
            // Map Tool API output types to FunctionCall types.
            $type = $this->mapToolTypeToContextType($output_def->getDataType());
            $description = $output_def->getDescription() ?? '';

            $output_definitions[$key] = new ContextDefinition(
              $type,
              $output_def->getLabel(),
              FALSE,
              FALSE,
              $description,
              NULL,
              [],
            );
          }
        }

        $definition['output_definitions'] = $output_definitions;
        $definitions[$tool_id] = $definition;
      }

      $this->derivatives = $definitions;
    }

    return parent::getDerivativeDefinitions($base_plugin_definition);
  }

  /**
   * Maps Tool API data types to Context API data types.
   *
   * @param string $tool_type
   *   The Tool API data type.
   *
   * @return string
   *   The Context API data type.
   */
  protected function mapToolTypeToContextType(string $tool_type): string {
    return match ($tool_type) {
      'float', 'integer' => 'float',
      'boolean' => 'boolean',
      'list', 'array' => 'string',
      'object' => 'string',
      default => 'string',
    };
  }

}
