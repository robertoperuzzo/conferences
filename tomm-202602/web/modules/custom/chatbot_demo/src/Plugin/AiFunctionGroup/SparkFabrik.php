<?php

declare(strict_types=1);

namespace Drupal\chatbot_demo\Plugin\AiFunctionGroup;

use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\ai\Attribute\FunctionGroup;
use Drupal\ai\Service\FunctionCalling\FunctionGroupInterface;

/**
 * The SparkFabrik agents.
 */
#[FunctionGroup(
  id: 'sparkfabrik',
  group_name: new TranslatableMarkup('SparkFabrik'),
  description: new TranslatableMarkup('These exposes tools from SparkFabrik.'),
  weight: -10,
)]
final class SparkFabrik implements FunctionGroupInterface {
}
