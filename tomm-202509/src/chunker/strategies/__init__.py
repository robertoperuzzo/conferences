"""Strategy implementations package.

This package contains all concrete chunking strategy implementations.
"""

from .fixed_size import FixedSizeChunker
from .sliding_langchain import SlidingLangChainChunker
from .sliding_unstructured import SlidingUnstructuredChunker
from .semantic import SemanticChunker

__all__ = [
    'FixedSizeChunker',
    'SlidingLangChainChunker',
    'SlidingUnstructuredChunker',
    'SemanticChunker'
]


# Strategy registry for dynamic loading
STRATEGY_REGISTRY = {
    'fixed_size': FixedSizeChunker,
    'sliding_langchain': SlidingLangChainChunker,
    'sliding_unstructured': SlidingUnstructuredChunker,
    'semantic': SemanticChunker
}


def get_strategy_class(strategy_name: str):
    """Get strategy class by name.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Strategy class
        
    Raises:
        ValueError: If strategy is not found
    """
    if strategy_name not in STRATEGY_REGISTRY:
        available = ', '.join(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Unknown strategy '{strategy_name}'. "
            f"Available strategies: {available}"
        )
    
    return STRATEGY_REGISTRY[strategy_name]
