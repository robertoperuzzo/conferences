<?php

declare(strict_types=1);

namespace Drupal\config_inspector;

final class ConfigSchemaValidatability {

  private $constraints = [];
  private $results = [];

  public function __construct(string $property_path, array $constraints) {
    assert(array_key_exists('local', $constraints) && array_key_exists('inherited', $constraints));
    $this->constraints[$property_path] = $constraints;
    $this->results[$property_path] = !empty($constraints['local']) || !empty($constraints['inherited']);
  }

  /**
   * Merges other validatability; not necessarily of the same root property path.
   *
   * @param self $other
   *   Another validatability.
   *
   * @return self
   *   A new ConfigSchemaValidatability object, with the merged data.
   */
  public function add(self $other): self {
    $this->results = array_merge($this->results, $other->results);
    ksort($this->results);
    $this->constraints = array_merge($this->constraints, $other->constraints);
    ksort($this->constraints);
    return $this;
  }

  public static function empty(): self {
    return new static('', FALSE);
  }

  public function getUnvalidatablePropertyPaths(?string $strip_parent_property_path = NULL): array {
    $unvalidatable_subset = array_filter($this->results, function (bool $is_validatable): bool {
      return !$is_validatable;
    });
    $unvalidatable_property_paths = array_keys($unvalidatable_subset);
    if ($strip_parent_property_path) {
      $unvalidatable_property_paths = str_replace($strip_parent_property_path, '', $unvalidatable_property_paths);
    }
    return $unvalidatable_property_paths;
  }

  public function isComplete(): bool {
    return $this->computePercentage() == 1.0;
  }

  public function computePercentage(): float {
    return round(count(array_filter($this->results)) / count($this->results), 2);
  }

  public function getValidatabilityPerPropertyPath(): array {
    return $this->results;
  }

  public function getConstraints(string $property_path): array {
    return $this->constraints[$property_path];
  }

  public function __toString(): string {
    $representation = '';

    $representation .= sprintf(
      "ℹ️ %0.2f%% validatable property paths (%d of %d property paths — this excludes property paths for base types)\n",
      100 * $this->computePercentage(),
      count(array_filter($this->results)),
      count($this->results)
    );

    $indentation_parents = [];
    foreach ($this->results as $property_path => $is_validatable) {
      $relative_property_path = $property_path;
      while (!empty($indentation_parents)) {
        if (str_starts_with($property_path, implode('.', $indentation_parents) . '.')) {
          $relative_property_path = str_replace(implode('.', $indentation_parents) . '.', '', $property_path);
          $indentation_parents[] = $relative_property_path;
          break;
        }
        else {
          array_pop($indentation_parents);
        }
      }

      $representation .= sprintf("%s%s %s\n",
        str_repeat('  ', count($indentation_parents)),
        $is_validatable ? '✅' : '❌',
        $relative_property_path,
      );

      // Prepare for the next iteration.
      if ($relative_property_path == $property_path) {
        $indentation_parents[] = $relative_property_path;
      }
    }

    return $representation;
  }

}
