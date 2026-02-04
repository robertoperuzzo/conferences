"""
Collection manager for Typesense collections.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CollectionManager:
    """Manages Typesense collections for indexing."""
    
    def __init__(self, typesense_client, default_schema_template: Dict[str, Any]):
        """Initialize collection manager."""
        self.client = typesense_client
        self.default_schema_template = default_schema_template
    
    def create_collection_schema(self, collection_name: str,
                                extraction_method: str,
                                chunking_strategy: str,
                                embedding_dimensions: int = 384) -> Dict[str, Any]:
        """Create collection schema for the given parameters."""
        schema = {
            "name": collection_name,
            "fields": []
        }
        
        # Copy fields from template
        for field in self.default_schema_template["fields"]:
            field_copy = field.copy()
            
            # Update embedding dimensions if needed
            if field_copy["name"] == "embedding":
                field_copy["num_dim"] = embedding_dimensions
            
            schema["fields"].append(field_copy)
        
        # Set default sorting field
        schema["default_sorting_field"] = "chunk_index"
        
        return schema
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        try:
            self.client.collections[collection_name].retrieve()
            return True
        except Exception:
            return False
    
    def create_collection(self, collection_name: str,
                         extraction_method: str,
                         chunking_strategy: str,
                         embedding_dimensions: int = 384,
                         force_recreate: bool = False) -> bool:
        """Create or recreate a collection."""
        try:
            if self.collection_exists(collection_name):
                if force_recreate:
                    logger.info(f"Deleting existing collection: {collection_name}")
                    self.client.collections[collection_name].delete()
                else:
                    logger.info(f"Collection {collection_name} already exists")
                    return True
            
            schema = self.create_collection_schema(
                collection_name, extraction_method, chunking_strategy,
                embedding_dimensions
            )
            
            logger.info(f"Creating collection: {collection_name}")
            self.client.collections.create(schema)
            
            # Verify creation
            if self.collection_exists(collection_name):
                logger.info(f"Collection {collection_name} created successfully")
                return True
            else:
                logger.error(f"Failed to verify collection creation: {collection_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            if self.collection_exists(collection_name):
                logger.info(f"Deleting collection: {collection_name}")
                self.client.collections[collection_name].delete()
                return True
            else:
                logger.warning(f"Collection {collection_name} does not exist")
                return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection statistics."""
        try:
            if not self.collection_exists(collection_name):
                return None
            
            collection_info = self.client.collections[collection_name].retrieve()
            return {
                "name": collection_info.get("name"),
                "num_documents": collection_info.get("num_documents", 0),
                "created_at": collection_info.get("created_at"),
                "num_memory_shards": collection_info.get("num_memory_shards", 0)
            }
        except Exception as e:
            logger.error(f"Error getting stats for collection {collection_name}: {e}")
            return None
