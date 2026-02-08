<?php

namespace Drupal\drupalcamp_rome\Plugin\tool\Tool;

use Drupal\commerce_cart\CartManagerInterface;
use Drupal\commerce_cart\CartProviderInterface;
use Drupal\commerce_product\Entity\ProductVariationInterface;
use Drupal\commerce_store\CurrentStoreInterface;
use Drupal\Component\Plugin\Exception\InvalidPluginDefinitionException;
use Drupal\Component\Plugin\Exception\PluginNotFoundException;
use Drupal\Core\Access\AccessResult;
use Drupal\Core\Access\AccessResultInterface;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\tool\Attribute\Tool;
use Drupal\tool\ExecutableResult;
use Drupal\tool\Tool\ToolBase;
use Drupal\tool\Tool\ToolOperation;
use Drupal\tool\TypedData\InputDefinition;
use Psr\Log\LoggerInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Plugin to add a product to the shopping cart.
 */
#[Tool(
  id: 'chatbot_demo:add_to_cart',
  label: new TranslatableMarkup('Add Product to Cart'),
  description: new TranslatableMarkup('Adds a product to the shopping cart by product variation SKU or UUID.'),
  // @phpstan-ignore-next-line
  operation: ToolOperation::Write,
  input_definitions: [
    'sku' => new InputDefinition(
      data_type: 'string',
      label: new TranslatableMarkup('Product SKU'),
      description: new TranslatableMarkup("The product variation SKU to add to cart (e.g., 'SHIRT-001')."),
      required: FALSE,
    ),
    'uuid' => new InputDefinition(
      data_type: 'string',
      label: new TranslatableMarkup('Product UUID'),
      description: new TranslatableMarkup('The product variation UUID to add to cart.'),
      required: FALSE
    ),
    'quantity' => new InputDefinition(
      data_type: 'string',
      label: new TranslatableMarkup('Quantity'),
      description: new TranslatableMarkup('The quantity of the product to add.'),
      required: FALSE,
      default_value: '1'
    ),
    'combine' => new InputDefinition(
      data_type: 'boolean',
      label: new TranslatableMarkup('Combine'),
      description: new TranslatableMarkup('Whether to combine with existing cart items if matching.'),
      required: FALSE,
      default_value: TRUE
    ),
  ],
  output_definitions: [
    'order_item_id' => new ContextDefinition(
      data_type: 'integer',
      label: new TranslatableMarkup('Order Item ID'),
      // @phpstan-ignore-next-line
      description: new TranslatableMarkup('The ID of the created or updated order item in the cart.')
    ),
  ],
)]
class AddToCart extends ToolBase {

  /**
   * The logger service.
   */
  private LoggerInterface $logger;

  /**
   * The Entity Type Manager service.
   */
  private EntityTypeManagerInterface $entityTypeManager;

  /**
   * The current store service.
   */
  private CurrentStoreInterface $currentStore;

  private CartProviderInterface $cartProvider;

  private CartManagerInterface $cartManager;

  /**
   * {@inheritdoc}
   */
  public static function create(
    ContainerInterface $container,
    array $configuration,
    $plugin_id,
    $plugin_definition
  ): static {
    $instance = parent::create($container, $configuration, $plugin_id, $plugin_definition);

    $logger = $container->get('logger.channel.tool');
    assert($logger instanceof LoggerInterface);
    $instance->logger = $logger;

    $entity_type_manager = $container->get('entity_type.manager');
    assert($entity_type_manager instanceof EntityTypeManagerInterface);
    $instance->entityTypeManager = $entity_type_manager;

    $current_store = $container->get('commerce_store.current_store');
    assert($current_store instanceof CurrentStoreInterface);
    $instance->currentStore = $current_store;

    $cart_provider = $container->get('commerce_cart.cart_provider');
    assert($cart_provider instanceof CartProviderInterface);
    $instance->cartProvider = $cart_provider;

    $cart_manager = $container->get('commerce_cart.cart_manager');
    assert($cart_manager instanceof CartManagerInterface);
    $instance->cartManager = $cart_manager;

    return $instance;

  }

  /**
   * {@inheritdoc}
   *
   * @phpstan-param array<array-key, mixed> $values
   */
  protected function doExecute(array $values): ExecutableResult {
    [
      'sku' => $sku,
      'uuid' => $uuid,
      'quantity' => $quantity,
      'combine' => $combine,
    ] = $values;

    // Validate that at least one identifier is provided.
    if (($sku === NULL || $sku === '') && ($uuid === NULL || $uuid === '')) {
      return ExecutableResult::failure(
        message: $this->t("Error: Either 'sku' or 'uuid' must be provided."),
      );
    }

    // Load product variation.
    $variation = $this->loadVariationByProperty(['sku' => $sku]);
    if ($variation === NULL) {
      $variation = $this->loadVariationByProperty(['uuid' => $uuid]);
    }

    if ($variation === NULL) {
      return ExecutableResult::failure(
        message: $this->t("Error: Product variation with SKU '@sku' or UUID '@uuid' not found.", ['@sku' => $sku, '@uuid' => $uuid]),
      );
    }

    // Validate variation is purchasable.
    if (!$variation->isPublished()) {
      return ExecutableResult::failure(
        message: $this->t("Error: Product variation '@title' is not available for purchase.", ['@title' => $variation->getTitle()]),
      );
    }

    $store = $this->currentStore->getStore();
    // Get or create cart.
    $cart = $this->cartProvider->getCart('default', $store);
    if ($cart === NULL) {
      $cart = $this->cartProvider->createCart('default', $store);
    }

    // Add to cart.
    try {
      $order_item = $this->cartManager->addEntity(
        $cart,
        $variation,
        $quantity,
        $combine
      );
    }
    catch (\Exception $e) {
      $this->logger->error('Error adding product variation to cart: @message', ['@message' => $e->getMessage()]);
      $identifier = !empty($sku) ? "SKU '$sku'" : "UUID '$uuid'";

      return ExecutableResult::failure(
        message: $this->t("Error adding product variation with @identifier to cart.", ['@identifier' => $identifier]),
      );
    }

    return ExecutableResult::success(
      message: $this->t("Product variation '@title' added to cart successfully.", ['@title' => $variation->getTitle()]),
      context_values: ['order_item_id' => $order_item->id()],
    );

  }

  /**
   * {@inheritdoc}
   *
   * @phpstan-param array<array-key, mixed> $values
   */
  protected function checkAccess(array $values, ?AccountInterface $account = NULL, mixed $return_as_object = FALSE): bool|AccessResultInterface {
    // Check for Commerce cart permissions.
    $result = AccessResult::allowedIfHasPermissions($account, [
      'access checkout',
      'view commerce_product',
    ], 'AND');

    return $return_as_object ? $result : $result->isAllowed();
  }

  /**
   * Helper method to load a product variation by SKU.
   *
   * @param array<string, string> $property
   *   The property to load by, e.g. ['sku' => 'SHIRT-001'] or ['uuid' => '123e4567-e89b-12d3-a456-426614174000'].
   *
   * @return \Drupal\commerce_product\Entity\ProductVariationInterface|null
   *   The loaded product variation, or NULL if not found.
   */
  private function loadVariationByProperty(array $property): ?ProductVariationInterface {
    try {
      $variation_storage = $this->entityTypeManager->getStorage('commerce_product_variation');
    } catch (InvalidPluginDefinitionException | PluginNotFoundException $e) {
      $this->logger->error('Error loading product variation storage: @message', ['@message' => $e->getMessage()]);
      return NULL;
    }
    $variations = $variation_storage->loadByProperties($property);

    if ($variations === []) {
      return NULL;
    }

    $variation = reset($variations);
    if (!$variation instanceof ProductVariationInterface) {
      return NULL;
    }

    return $variation;
  }

}
