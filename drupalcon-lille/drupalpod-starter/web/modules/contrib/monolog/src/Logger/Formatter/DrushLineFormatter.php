<?php

declare(strict_types=1);

namespace Drupal\monolog\Logger\Formatter;

use Monolog\Formatter\LineFormatter;

/**
 * Formatter suitable to be using with Drush logs.
 */
class DrushLineFormatter extends LineFormatter {

  /**
   * {@inheritdoc}
   */
  protected function convertToString($data): string {
    if (null === $data || is_bool($data)) {
      return var_export($data, true);
    }

    if (is_scalar($data)) {
      return (string) $data;
    }

    $result = "";
    array_walk($data, function($val, $key) use(&$result) {
      if ($val != "" && is_scalar($val)) {
        $result .= " | $key=$val";
      }
    });

    return ltrim($result);
  }

}
