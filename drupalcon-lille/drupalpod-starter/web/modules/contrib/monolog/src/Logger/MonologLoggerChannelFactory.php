<?php

declare(strict_types=1);

namespace Drupal\monolog\Logger;

use Monolog\Handler\HandlerInterface;
use Psr\Log\NullLogger;
use Psr\Log\LoggerInterface;
use Monolog\Formatter\FormatterInterface;
use Monolog\Handler\FormattableHandlerInterface;
use Monolog\Handler\ProcessableHandlerInterface;
use Drupal\Core\Logger\LoggerChannelFactoryInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\DependencyInjection\ContainerAwareTrait;
use Symfony\Component\DependencyInjection\ContainerAwareInterface;

/**
 * Defines a factory for logging channels.
 */
class MonologLoggerChannelFactory implements LoggerChannelFactoryInterface, ContainerAwareInterface {

  use ContainerAwareTrait;

  private const HANDLERS_KEY = 'monolog.channel_handlers';

  private const PROCESSORS_KEY = 'monolog.processors';

  private const HANDLER_PREFIX = 'monolog.handler.';

  private const FORMATTER_PREFIX = 'monolog.formatter.';

  private const PROCESSOR_PREFIX = 'monolog.processor.';

  /**
   * Array of all instantiated logger channels keyed by channel name.
   *
   * @var \Drupal\Core\Logger\LoggerChannelInterface[]
   */
  protected array $channels = [];

  /**
   * Array of all instantiated handlers keyed by a hash of their configuration.
   *
   * @var \Monolog\Handler\HandlerInterface[]
   */
  protected array $handlers = [];

  /**
   * Array of enabled processors.
   *
   * @var array
   */
  protected array $enabledProcessors;

  /**
   * {@inheritdoc}
   */
  public function get($channel) {
    if (!isset($this->channels[$channel])) {
      try {
        $this->channels[$channel] = $this->getChannelInstance($channel);
      }
      catch (\InvalidArgumentException $e) {
        $this->channels[$channel] = new NullLogger();
        if ($this->container->get('current_user')
          ->hasPermission('administer site configuration')) {
          \Drupal::messenger()->addError($e->getMessage());
        }
      }
    }

    return $this->channels[$channel];
  }

  /**
   * {@inheritdoc}
   */
  public function addLogger(LoggerInterface $logger, $priority = 0) {
    /* No-op, we have handlers which are services and configured in the
    services.yml file. */
    // @see https://www.drupal.org/node/2411683
  }

  /**
   * Factory function for Monolog loggers.
   *
   * @param string $channel_name
   *   The name the logging channel.
   *
   * @return \Psr\Log\LoggerInterface
   *   Describes a logger instance.
   *
   * @throws \RuntimeException
   * @throws \InvalidArgumentException
   */
  protected function getChannelInstance(string $channel_name): LoggerInterface {
    if (!class_exists('Monolog\Logger')) {
      throw new \RuntimeException('The Monolog\Logger class was not found. Make sure the Monolog package is installed via Composer.');
    }

    return $this->getContainer()
      ->bind(fn($x) => $this->getParameters($x))
      ->bind(fn($x) => $this->getHandlers($x, $channel_name))
      ->bind(fn($x) => $this->getLogger($x, $channel_name))
      ->get();
  }

  /**
   * Get the service container or null.
   *
   * @return \Drupal\monolog\Logger\OptionalLogger
   *   The service container or null.
   */
  private function getContainer(): OptionalLogger {
    return $this->container
      ? OptionalLogger::of($this->container)
      : OptionalLogger::none();
  }

  /**
   * Get the `monolog.channel_handlers` parameter or null.
   *
   * @param \Symfony\Component\DependencyInjection\ContainerInterface $container
   *   The service container.
   *
   * @return \Drupal\monolog\Logger\OptionalLogger
   *   The `monolog.channel_handlers` parameter or null.
   */
  private function getParameters(ContainerInterface $container): OptionalLogger {
    if ($container->hasParameter(self::HANDLERS_KEY)) {
      $parameters = $container->getParameter(self::HANDLERS_KEY);

      if (is_array($parameters)) {
        return OptionalLogger::of($parameters);
      }
    }

    return OptionalLogger::none();
  }

  /**
   * Get the configured handlers for the channel or null.
   *
   * @param array $parameters
   *   The `monolog.channel_handlers` parameter.
   * @param string $channel_name
   *   The channel's name.
   *
   * @return \Drupal\monolog\Logger\OptionalLogger
   *   The configured handlers for the channel or null.
   */
  private function getHandlers(
    array $parameters,
    string $channel_name
  ): OptionalLogger {
    // Get config for this channel (or fallback to `default`).
    if (array_key_exists($channel_name, $parameters)) {
      $config = $parameters[$channel_name];
    }
    else {
      if (array_key_exists('default', $parameters)) {
        $config = $parameters['default'];
      }
      else {
        return OptionalLogger::none();
      }
    }

    // Config must be an array.
    if (!is_array($config)) {
      return OptionalLogger::none();
    }

    // Extract handlers configuration.
    $handlers = [];

    // Simple syntax.
    if (!array_key_exists('handlers', $config)) {
      $handlers = array_map(function (string $handler): array {
        return [
          'name' => $handler,
          'formatter' => NULL,
          'processors' => $this->container->getParameter(self::PROCESSORS_KEY),
        ];
      }, $config);
    }

    // Nested syntax.
    if (array_key_exists('handlers', $config)) {
      try {
        $handlers = array_map(function (array $handler): array {
          return [
            'name' => $handler['name'] ?? $handler,
            'formatter' => $handler['formatter'] ?? NULL,
            'processors' => $handler['processors'] ?? $this->container->getParameter(self::PROCESSORS_KEY),
          ];
        }, $config['handlers']);
      }
      catch (\Throwable $e) {
        return OptionalLogger::none();
      }
    }

    if (empty($handlers)) {
      return OptionalLogger::none();
    }

    return OptionalLogger::of($handlers);
  }

  /**
   * Get a Logger instance or null.
   *
   * @param array $handlers
   *   The configured handlers for the channel.
   * @param string $channel_name
   *   The channel's name.
   *
   * @return \Drupal\monolog\Logger\OptionalLogger
   *   A Logger instance or null.
   */
  private function getLogger(array $handlers, string $channel_name): OptionalLogger {
    $logger = new Logger($channel_name);

    // For each handler, configure it and add it to the logger.
    array_walk($handlers, function (array $handler) use ($logger) {
      $h = $this->getHandler($handler);
      if ($h != NULL) {
        $logger->pushHandler($h);
      }
    });

    return OptionalLogger::of($logger);
  }

  /**
   * Get a handler instance for given configuration or null.
   *
   * Only a single handler will be instantiated per unique configuration,
   * allowing handlers to be reused for multiple logger channels.
   *
   * @param array $handler
   *   The handler configuration.
   *
   * @return \Monolog\Handler\HandlerInterface
   *   A handler instance or null.
   */
  private function getHandler(array $handler): ?HandlerInterface {
    $configuration_hash = json_encode($handler);
    if (!isset($this->handlers[$configuration_hash])) {
      $h = $this->container->get(self::HANDLER_PREFIX . $handler['name']);

      // If the handler is a formattable handler, set the formatter.
      $formatter = $handler['formatter'];
      if ($h instanceof FormattableHandlerInterface && $formatter && $this->container->has(self::FORMATTER_PREFIX . $formatter)) {
        $f = $this->container->get(self::FORMATTER_PREFIX . $formatter);
        if ($f instanceof FormatterInterface) {
          $h->setFormatter($f);
        }
      }

      // If the handler is a processable handler, set the processors.
      $processors = $handler['processors'];
      if ($h instanceof ProcessableHandlerInterface && $processors) {
        foreach ($processors as $processor) {
          $p = $this->container->get(self::PROCESSOR_PREFIX . $processor);

          if (is_callable($p)) {
            $h->pushProcessor($p);
          }
        }
      }

      $this->handlers[$configuration_hash] = $h;
    }

    return $this->handlers[$configuration_hash];
  }

}
