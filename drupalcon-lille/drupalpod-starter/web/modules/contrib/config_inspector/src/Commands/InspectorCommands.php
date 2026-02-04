<?php

namespace Drupal\config_inspector\Commands;

use Consolidation\AnnotatedCommand\CommandResult;
use Consolidation\OutputFormatters\StructuredData\MetadataInterface;
use Consolidation\OutputFormatters\StructuredData\RowsOfFields;
use Consolidation\OutputFormatters\StructuredData\UnstructuredListData;
use Drupal\Component\Serialization\Yaml;
use Drupal\config_inspector\ConfigInspectorManager;
use Drupal\config_inspector\ConfigSchemaValidatability;
use Drupal\Core\Config\StorageInterface;
use Drush\Commands\DrushCommands;
use Symfony\Component\Validator\Constraint;

/**
 * Provides commands for config inspector.
 */
class InspectorCommands extends DrushCommands {

  /**
   * The configuration inspector manager.
   *
   * @var \Drupal\config_inspector\ConfigInspectorManager
   */
  protected $inspector;

  /**
   * The active configuration storage.
   *
   * @var \Drupal\Core\Config\StorageInterface
   */
  protected $activeStorage;

  /**
   * Constructs InspectorCommands object.
   *
   * @param \Drupal\config_inspector\ConfigInspectorManager $config_inspector_manager
   *   The configuration inspector manager.
   * @param \Drupal\Core\Config\StorageInterface $storage
   *   The active configuration storage.
   */
  public function __construct(ConfigInspectorManager $config_inspector_manager, StorageInterface $storage) {
    parent::__construct();
    $this->inspector = $config_inspector_manager;
    $this->activeStorage = $storage;
  }

  /**
   * Inspect config for schema errors.
   *
   * @param string $key
   *   (Optional) Configuration key.
   * @param array $options
   *   (Optional) Options array.
   *
   * @return \Consolidation\OutputFormatters\StructuredData\RowsOfFields
   *   List of inspections.
   *
   * @option only-error
   *   Display only errors.
   * @option detail
   *   Show details.
   * @option skip-keys
   *   Configuration keys to skip. Cannot be used together with filter-keys.
   * @option filter-keys
   *   Configuration keys to filter. Cannot be used together with skip-keys.
   * @option strict-validation
   *   Treat <100% validatability as an error.
   * @option list-constraints
   *   List validation constraints. Requires --detail.
   *
   * @usage drush config:inspect
   *   Inspect whole config for schema errors.
   * @usage drush config:inspect --only-error
   *   Inspect whole config for schema errors, but do not show valid config.
   * @usage drush config:inspect --detail
   *   Inspect whole config for schema errors but details errors.
   * @usage drush config:inspect --only-error --detail
   *   Inspect whole config for schema errors and display only errors if any.
   * @usage drush config:inspect --only-error --strict-validation
   *   Inspect whole config for schema errors and incomplete validatability.
   * @usage drush config:inspect --only-error --strict-validation --filter-keys=media.settings,system.theme.global
   *   Inspect only media.settings and system.theme.global config for schema and
   *   validatability errors.
   *
   * @field-labels
   *   key: Key
   *   status: Status
   *   validatability: Validatable
   *   data: Data
   *   constraints: Validation constraints
   * @default-fields key,status,validatability,data,constraints
   * @metadata-template <comment> Legend for Data:</comment> {legend}
   *
   * @command config:inspect
   * @aliases inspect_config
   */
  public function inspect($key = '', array $options = [
    'only-error' => FALSE,
    'detail' => FALSE,
    'skip-keys' => self::OPT,
    'filter-keys' => self::OPT,
    'strict-validation' => FALSE,
    'list-constraints' => FALSE,
  ]) {
    if ($options['skip-keys'] && $options['filter-keys']) {
      throw new \Exception('Cannot use both --skip-keys and --filter-keys. Use either or neither, not both.');
    }
    if ($options['list-constraints'] && !$options['detail']) {
      throw new \Exception('Cannot use --list-constraints without --detail.');
    }

    $rows = [];
    $exitCode = self::EXIT_SUCCESS;
    $keys = empty($key) ? $this->activeStorage->listAll() : [$key];
    $onlyError = $options['only-error'];
    $detail = $options['detail'];
    $strict_validation = $options['strict-validation'];
    $skipKeys = !isset($options['skip-keys']) ? [] : array_fill_keys(explode(',', $options['skip-keys']), '1');
    $filterKeys = !isset($options['filter-keys']) ? [] : array_fill_keys(explode(',', $options['filter-keys']), '1');
    $listConstraints = $options['list-constraints'];

    foreach ($keys as $name) {
      if (isset($skipKeys[$name])) {
        continue;
      }
      if (!empty($filterKeys) && !isset($filterKeys[$name])) {
        continue;
      }
      $has_schema = $this->inspector->hasSchema($name);
      if (!$has_schema) {
        $status = dt('No schema');
        $validatability = NULL;
        $data = NULL;
      }
      else {
        $result = $this->inspector->checkValues($name);
        $has_valid_schema = !is_array($result);
        // 1. Schema status.
        if (!$has_valid_schema) {
          $exitCode = self::EXIT_FAILURE;
          if ($detail) {
            foreach ($result as $key => $error) {
              $rows[$key] = ['key' => $key, 'status' => $error, 'validatability' => NULL, 'data' => NULL];
            }
            // Require the schema to be fixed before checking validatability.
            continue;
          }
          else {
            $status = dt('@count errors', ['@count' => count($result)]);
            $validatability = NULL;
            $data = NULL;
          }
        }
        else {
          $status = dt('Correct');
          $validatability_detail = [];
          $data_detail = [];
          $all_property_paths = [];

          // 2. Schema validatability.
          $raw_validatability = $this->inspector->checkValidatabilityValues($name);
          $all_property_paths = array_keys($raw_validatability->getValidatabilityPerPropertyPath());
          if ($detail) {
            foreach ($raw_validatability->getValidatabilityPerPropertyPath() as $property_path => $is_validatable) {
              $relative_property_path = self::getRelativePropertyPath($name, $property_path);
              $key = "$name:$relative_property_path";
              $validatability_detail[$key] = $is_validatable;
            }
          }
          // Continue to validating the data: even with incomplete
          // validatability that is valuable to check.
          $validatability = dt('@validatability%', ['@validatability' => intval($raw_validatability->computePercentage() * 100)]);

          // 3. Schema validation constraint violations.
          $raw_violations = $this->inspector->validateValues($name);
          $has_valid_data = $raw_violations->count() === 0;
          if ($detail) {
            $violations = ConfigInspectorManager::violationsToArray($raw_violations);
            foreach ($all_property_paths as $property_path) {
              $relative_property_path = self::getRelativePropertyPath($name, $property_path);
              $key = "$name:$relative_property_path";
              $data_detail[$key] = !isset($violations[$property_path]) ? TRUE : $violations[$property_path];
            }
          }
          $data = $has_valid_data
            ? $raw_validatability->isComplete() ? '✅✅' : '✅❓'
            : dt('@count errors', ['@count' => $raw_violations->count()]);
        }
      }

      // Respect --only-error (failure on any of the 3 is considered an error).
      if ($onlyError && $has_schema && ($has_valid_schema && $has_valid_data && (!$strict_validation || $raw_validatability->isComplete()))) {
        continue;
      }
      $rows[$name] = ['key' => $name, 'status' => $status, 'validatability' => $validatability, 'data' => $data];
      if ($listConstraints) {
        // @todo Remove once <= 10.0.x support is dropped.
        $property_path = $name;
        if (version_compare(\Drupal::VERSION, '10.1.0', 'lt')) {
          $property_path = '';
        }
        $rows[$name]['constraints'] = implode("\n", self::getPrintableConstraints($raw_validatability, $property_path));
      }

      // Show a detailed view if requested.
      if ($detail) {
        foreach ($all_property_paths as $property_path) {
          $relative_property_path = self::getRelativePropertyPath($name, $property_path);
          $key = "$name:$relative_property_path";

          // Again respect --only-error:
          if ($onlyError
            // - only show keys whose data is invalid
            && $data_detail[$key] === TRUE
            // - or, if --strict-validation is specified, also show keys  whose data is not
            // validatable.
            && (!$strict_validation || $validatability_detail[$key] === TRUE)
          ) {
            continue;
          }

          $rows[$key] = [
            'key' => " $key",
            'status' => $status,
            'validatability' => $validatability_detail[$key] ? dt('Validatable') : dt('NOT'),
            'data' => $validatability_detail[$key]
               ? $data_detail[$key] === TRUE ? '✅✅' : $data_detail[$key]
               : '✅❓',
          ];


          if ($listConstraints) {
            // @todo Remove once <= 10.0.x support is dropped.
            if (version_compare(\Drupal::VERSION, '10.1.0', 'lt')) {
              $property_path = str_replace("$name.", '', $property_path);
            }
            $rows[$key]['constraints'] = implode("\n", self::getPrintableConstraints($raw_validatability, $property_path));
          }
        }
      }
    }

    // Provide a legend if the "data" field is displayed.
    if (in_array('data', explode(',', $options['fields']), TRUE)) {
      return CommandResult::dataWithExitCode(new RowsOfFieldsWithLegend($rows), $exitCode);
    }

    return CommandResult::dataWithExitCode(new RowsOfFields($rows), $exitCode);
  }

  private static function getRelativePropertyPath(string $config_name, string $absolute_property_path): string {
    return $absolute_property_path === $config_name
      // The root.
      ? ''
      // All other property paths.
      : str_replace("$config_name.", '', $absolute_property_path);
  }

  /**
   * Maps the validation constraints for the given property path to strings.
   *
   * @param \Drupal\config_inspector\ConfigSchemaValidatability $validatability
   *   The validatability of a config schema.
   * @param string $property_path
   *   The property path for which to retrieve the constraints.
   *
   * @return string[]
   *   Printable constraints.
   */
  private static function getPrintableConstraints(ConfigSchemaValidatability $validatability, string $property_path): array {
    $all_constraints = $validatability->getConstraints($property_path);
    $local_constraints = array_map(
      fn (string $constraint_name, $constraints_options) => trim(Yaml::encode([$constraint_name => $constraints_options])),
      array_keys($all_constraints['local']),
      array_values($all_constraints['local'])
    );
    $inherited_constraints = array_map(
      fn (string $constraint_name, $constraints_options) => "↣ " . trim(Yaml::encode([$constraint_name => $constraints_options])),
      array_keys($all_constraints['inherited']),
      array_values($all_constraints['inherited'])
    );

    return array_merge($local_constraints, $inherited_constraints);
  }

}

class RowsOfFieldsWithLegend extends RowsOfFields implements MetadataInterface {

  public function getMetadata() {
    $legend = <<<EOL

  ✅❓  → Correct primitive type, detailed validation impossible.
  ✅✅  → Correct primitive type, passed all validation constraints.
EOL;
    return ['legend' => $legend];
  }
};
