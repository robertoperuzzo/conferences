<?php

namespace Drupal\drupalcamp_rome\Plugin\AiFunctionCall;

use Drupal\ai\Attribute\FunctionCall;
use Drupal\ai\Base\FunctionCallBase;
use Drupal\ai\PluginManager\AiDataTypeConverterPluginManager;
use Drupal\ai\Service\FunctionCalling\ExecutableFunctionCallInterface;
use Drupal\ai\Utility\ContextDefinitionNormalizer;
use Drupal\commerce_cart\CartManagerInterface;
use Drupal\commerce_cart\CartProviderInterface;
use Drupal\commerce_store\CurrentStoreInterface;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Plugin to add a product to the shopping cart.
 */
#[FunctionCall(
  id: 'drupalcamp_rome:add_to_cart',
  function_name: 'add_to_cart',
  name: 'Add Product to Cart',
  description: 'Adds a product to the shopping cart by product variation SKU or UUID.',
  group: 'drupalcamp_rome',
  context_definitions: [
    'sku' => new ContextDefinition(
      data_type: 'string',
      label: new TranslatableMarkup("Product SKU"),
      required: FALSE,
      description: new TranslatableMarkup("The product variation SKU to add to cart (e.g., 'SHIRT-001').")
    ),
    'uuid' => new ContextDefinition(
      data_type: 'string',
      label: new TranslatableMarkup("Product UUID"),
      required: FALSE,
      description: new TranslatableMarkup("The product variation UUID to add to cart.")
    ),
    'quantity' => new ContextDefinition(
      data_type: 'string',
      label: new TranslatableMarkup("Quantity"),
      required: FALSE,
      description: new TranslatableMarkup("The quantity of the product to add."),
      default_value: '1'
    ),
    'combine' => new ContextDefinition(
      data_type: 'boolean',
      label: new TranslatableMarkup("Combine"),
      required: FALSE,
      description: new TranslatableMarkup("Whether to combine with existing cart items if matching."),
      default_value: TRUE
    ),
  ]
)]
class AddToCart extends FunctionCallBase implements ExecutableFunctionCallInterface {

  /**
   * {@inheritdoc}
   */
  public function __construct(
    array $configuration,
    $plugin_id,
    $plugin_definition,
    ContextDefinitionNormalizer $context_definition_normalizer,
    AiDataTypeConverterPluginManager $data_type_converter_manager,
    protected ?EntityTypeManagerInterface $entityTypeManager = NULL,
    protected ?CartManagerInterface $cartManager = NULL,
    protected ?CartProviderInterface $cartProvider = NULL,
    protected ?AccountInterface $currentUser = NULL,
    protected ?CurrentStoreInterface $currentStore = NULL,
  ) {
    parent::__construct(
      $configuration,
      $plugin_id,
      $plugin_definition,
      $context_definition_normalizer,
      $data_type_converter_manager
    );
  }

  /**
   * {@inheritdoc}
   */
  public static function create(
    ContainerInterface $container,
    array $configuration,
    $plugin_id,
    $plugin_definition
  ): static {
    return new static(
      $configuration,
      $plugin_id,
      $plugin_definition,
      $container->get('ai.context_definition_normalizer'),
      $container->get('plugin.manager.ai_data_type_converter'),
      $container->get('entity_type.manager'),
      $container->get('commerce_cart.cart_manager'),
      $container->get('commerce_cart.cart_provider'),
      $container->get('current_user'),
      $container->get('commerce_store.current_store'),
    );
  }

  /**
   * {@inheritdoc}
   */
  public function execute(): void {
    // Initialize output.
    $this->stringOutput = '';

    // Retrieve context values.
    $sku = $this->getContextValue('sku');
    $uuid = $this->getContextValue('uuid');
    $quantity = $this->getContextValue('quantity');
    $combine = $this->getContextValue('combine');

    // Validate that at least one identifier is provided.
    if (empty($sku) && empty($uuid)) {
      $this->stringOutput = "Error: Either 'sku' or 'uuid' must be provided.";
      return;
    }

    // Load product variation.
    $variation_storage = $this->entityTypeManager->getStorage('commerce_product_variation');
    $variation = NULL;

    // Try loading by SKU first (more common use case).
    if (!empty($sku)) {
      $variations = $variation_storage->loadByProperties(['sku' => $sku]);
      if (!empty($variations)) {
        $variation = reset($variations);
      }
      else {
        $this->stringOutput = "Error: Product variation with SKU '{$sku}' not found.";
        return;
      }
    }
    // Try loading by UUID if SKU not provided.
    elseif (!empty($uuid)) {
      $variations = $variation_storage->loadByProperties(['uuid' => $uuid]);
      if (!empty($variations)) {
        $variation = reset($variations);
      }
      else {
        $this->stringOutput = "Error: Product variation with UUID '{$uuid}' not found.";
        return;
      }
    }

    // Validate variation is purchasable.
    if (!$variation->isPublished()) {
      $this->stringOutput = "Error: Product variation is not available for purchase.";
      return;
    }

    // Get current store.
    $store = $this->currentStore->getStore();
    if (!$store) {
      $this->stringOutput = "Error: No store context available.";
      return;
    }

    // Get or create cart.
    $cart = $this->cartProvider->getCart('default', $store);
    if (!$cart) {
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

      $identifier = !empty($sku) ? "SKU '{$sku}'" : "UUID '{$uuid}'";
      $this->stringOutput = sprintf(
        'Successfully added %s x "%s" (%s) to cart. Order item ID: %s',
        $quantity,
        $variation->getTitle(),
        $identifier,
        $order_item->id()
      );
    }
    catch (\Exception $e) {
      $this->stringOutput = "Error adding to cart: " . $e->getMessage();
    }
  }

}
