#!/bin/bash
# This script launches a Drupal 11 site with Typesense integration using DDEV.
mkdir drupal-typesense && cd drupal-typesense
ddev config --project-type=drupal11 --docroot=web
ddev start
ddev composer create drupal/recommended-project:^11 --stability=dev --no-install
# Disallow non-allowed plugins by default, avoiding boring user interactions.
ddev composer config --no-plugins allow-plugins.* false
ddev composer update
ddev composer require drush/drush
ddev composer require drupal/ai
ddev composer require drupal/ai_provider_openai
ddev composer require drupal/search_api_typesense
ddev add-on get lussoluca/ddev-typesense
ddev restart
ddev drush site:install demo_umami --account-name=admin --account-pass=admin -y
ddev drush en search_api_typesense ai ai_provider_openai -y
ddev launch
