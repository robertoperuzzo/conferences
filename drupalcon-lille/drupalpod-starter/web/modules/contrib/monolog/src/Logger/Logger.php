<?php

declare(strict_types=1);

namespace Drupal\monolog\Logger;

use Symfony\Component\HttpFoundation\RequestStack;
use Drupal\Core\Logger\LoggerChannelInterface;
use Drupal\Core\Session\AccountInterface;
use Monolog\Logger as BaseLogger;
use Psr\Log\LoggerInterface;

/**
 * Logger class for the Drupal Monolog module.
 */
class Logger extends BaseLogger implements LoggerChannelInterface {

  /**
   * {@inheritdoc}
   */
  public function setRequestStack(RequestStack $requestStack = NULL) {
    // Do nothing, use a handler for this.
  }

  /**
   * {@inheritdoc}
   */
  public function setCurrentUser(AccountInterface $current_user = NULL) {
    // Do nothing, use a handler for this.
  }

  /**
   * {@inheritdoc}
   */
  public function setLoggers(array $loggers) {
    // Do nothing.
  }

  /**
   * {@inheritdoc}
   */
  public function addLogger(LoggerInterface $logger, $priority = 0) {
    // Do nothing.
  }

}
