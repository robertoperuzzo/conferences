"""
CLI interface for the Typesense indexer.
"""

import argparse
import logging
import sys
import os
from dotenv import load_dotenv

from .config import IndexerConfig
from .typesense_indexer import TypesenseIndexer


def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/workspace/logs/indexer.log', mode='a')
        ]
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Typesense Vector Indexer for Document Chunks'
    )

    parser.add_argument(
        '--index-all',
        action='store_true',
        help='Index all extraction methods and chunking strategies'
    )

    parser.add_argument(
        '--extraction-method',
        type=str,
        help='Specific extraction method to index'
    )

    parser.add_argument(
        '--chunking-strategy',
        type=str,
        help='Specific chunking strategy to index'
    )

    parser.add_argument(
        '--max-documents',
        type=int,
        default=5,
        help='Maximum number of documents to process (-1 for all)'
    )

    parser.add_argument(
        '--force-recreate',
        action='store_true',
        help='Force recreation of existing collections'
    )

    parser.add_argument(
        '--reindex',
        action='store_true',
        help='Reindex existing collections'
    )

    parser.add_argument(
        '--collection',
        type=str,
        help='Specific collection to reindex'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Log level'
    )

    parser.add_argument(
        '--list-methods',
        action='store_true',
        help='List available extraction methods'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show collection statistics'
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # Load and set up environment variables first
        load_dotenv()

        # Set default API key for development if not set in environment
        if not os.getenv('TYPESENSE_ADMIN_API_KEY'):
            os.environ['TYPESENSE_ADMIN_API_KEY'] = 'xyz'

        # Initialize configuration and indexer
        config = IndexerConfig()

        # Override defaults for development if needed
        if not config.typesense_api_key:
            config.typesense_api_key = 'xyz'
        # Don't override host - let it use the Docker service name from environment

        config.max_documents = args.max_documents

        indexer = TypesenseIndexer(config)

        # Handle different commands
        if args.list_methods:
            methods = indexer.data_processor.get_available_extraction_methods()
            logger.info(f"Available extraction methods: {methods}")
            return 0

        if args.stats:
            show_collection_stats(indexer)
            return 0

        if args.index_all:
            logger.info("Starting indexing of all combinations...")
            logger.info(f"Max documents: {args.max_documents}")
            logger.info(f"Force recreate: {args.force_recreate}")

            results = indexer.index_all_combinations(
                max_documents=args.max_documents,
                force_recreate=args.force_recreate
            )

            # Report results
            successful = sum(1 for success in results.values() if success)
            total = len(results)

            logger.info(f"Indexing completed: {successful}/{total} successful")

            for combination, success in results.items():
                status = "✓" if success else "✗"
                logger.info(f"  {status} {combination}")

            return 0 if successful == total else 1

        elif args.extraction_method and args.chunking_strategy:
            logger.info(
                f"Indexing {args.extraction_method}_{args.chunking_strategy}")

            success = indexer.index_extraction_method_strategy(
                args.extraction_method,
                args.chunking_strategy,
                max_documents=args.max_documents,
                force_recreate=args.force_recreate
            )

            if success:
                logger.info("Indexing completed successfully")
                return 0
            else:
                logger.error("Indexing failed")
                return 1

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        logger.info("Indexing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Indexing failed with error: {e}", exc_info=True)
        return 1


def show_collection_stats(indexer: TypesenseIndexer):
    """Show statistics for all collections."""
    logger = logging.getLogger(__name__)

    try:
        # Get all collections
        collections_response = indexer.client.collections.retrieve()
        collections = collections_response if isinstance(
            collections_response, list) else []

        if not collections:
            logger.info("No collections found")
            return

        logger.info(f"Found {len(collections)} collections:")

        for collection in collections:
            collection_name = collection.get('name', 'Unknown')
            stats = indexer.get_collection_stats(collection_name)

            if stats:
                num_docs = stats.get('num_documents', 0)
                created_at = stats.get('created_at', 'Unknown')
                logger.info(f"  {collection_name}: {num_docs} documents "
                            f"(created: {created_at})")
            else:
                logger.info(f"  {collection_name}: Unable to get stats")

    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")


if __name__ == '__main__':
    sys.exit(main())
