"""
Base indexer interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseIndexer(ABC):
    """Base class for document indexers."""
    
    @abstractmethod
    def create_collection(self, collection_name: str, schema: Dict[str, Any]) \
            -> bool:
        """Create a new collection with the given schema."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        pass
    
    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        pass
    
    @abstractmethod
    def index_documents(self, collection_name: str,
                       documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index a batch of documents."""
        pass
    
    @abstractmethod
    def search(self, collection_name: str, query: Dict[str, Any]) \
            -> Dict[str, Any]:
        """Perform a search query."""
        pass
    
    @abstractmethod
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection."""
        pass
