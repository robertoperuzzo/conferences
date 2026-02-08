<?php

declare(strict_types=1);

namespace Drupal\chatbot_demo\Plugin\AiFunctionGroup;

use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\ai\Attribute\FunctionGroup;
use Drupal\ai\Service\FunctionCalling\FunctionGroupInterface;

/**
 * The Drupal agents.
 */
#[FunctionGroup(
  id: 'chatbot_demo',
  group_name: new TranslatableMarkup('Chatbot Demo Tools'),
  description: new TranslatableMarkup('These exposes tools from the Chatbot Demo.'),
  weight: -10,
)]
final class ChatbotDemo implements FunctionGroupInterface {
}
