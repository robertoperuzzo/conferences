<?php

declare(strict_types=1);

namespace Drupal\drupalcamp_rome\Plugin\AiFunctionGroup;

use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\ai\Attribute\FunctionGroup;
use Drupal\ai\Service\FunctionCalling\FunctionGroupInterface;

/**
 * The Drupal agents.
 */
#[FunctionGroup(
  id: 'drupalcamp_rome',
  group_name: new TranslatableMarkup('DrupalCamp Rome Tools'),
  description: new TranslatableMarkup('These exposes tools from the DrupalCamp Rome.'),
  weight: -10,
)]
final class DrupalCampRome implements FunctionGroupInterface {
}
