"""Configuration management for chunking strategies.

This module provides configuration loading and validation for all
chunking strategies, extending the main project configuration.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Handle imports depending on context
try:
    from ..config import DATA_CHUNKS_PATH
except ImportError:
    # Fallback for standalone execution
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_CHUNKS_PATH = PROJECT_ROOT / "data" / "chunks"

from .models import ChunkingConfig


logger = logging.getLogger(__name__)


# Default chunking strategies configuration
DEFAULT_CHUNKING_CONFIG = {
    "enabled_strategies": [
        "fixed_size",
        "sliding_langchain",
        "sliding_unstructured",
        "semantic"
    ],
    "strategy_configs": {
        "fixed_size": {
            "chunk_size": 1000,
            "chars_per_token": 4.0
        },
        "sliding_langchain": {
            "chunk_size": 1000,
            "chunk_overlap": 80,
            "separators": ["\n\n", "\n", " ", ""],
            "keep_separator": False,
            "is_separator_regex": False
        },
        "sliding_unstructured": {
            "max_elements_per_chunk": 10,
            "overlap_percentage": 0.2,
            "priority_elements": ["Title", "Header", "NarrativeText"],
            "respect_boundaries": True
        },
        "semantic": {
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "similarity_threshold": 0.8,
            "min_chunk_size": 200,
            "max_chunk_size": 2000,
            "batch_size": 32
        }
    },
    "output_format": "json",
    "batch_size": 10,
    "max_workers": 4,
    "save_intermediate": True,
    "output_directory": str(DATA_CHUNKS_PATH)
}


class ChunkingConfigManager:
    """Manages configuration for chunking strategies."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional path to custom configuration file
        """
        self.config_path = config_path
        self._config = None

    def load_config(self) -> ChunkingConfig:
        """Load chunking configuration.

        Returns:
            ChunkingConfig object with loaded configuration
        """
        if self._config is not None:
            return self._config

        config_data = DEFAULT_CHUNKING_CONFIG.copy()

        # Load custom configuration if provided
        if self.config_path and self.config_path.exists():
            try:
                custom_config = self._load_config_file(self.config_path)
                config_data = self._merge_configs(config_data, custom_config)
                logger.info(f"Loaded custom config from {self.config_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to load custom config from "
                    f"{self.config_path}: {e}"
                )
                logger.info("Using default configuration")

        # Validate configuration
        config_data = self._validate_config(config_data)

        # Create ChunkingConfig object
        self._config = ChunkingConfig.from_dict(config_data)

        return self._config

    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dictionary with configuration data
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                return yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ValueError(
                    f"Unsupported config file format: {config_path.suffix}"
                )

    def _merge_configs(
        self,
        default_config: Dict[str, Any],
        custom_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge custom configuration with defaults.

        Args:
            default_config: Default configuration
            custom_config: Custom configuration to merge

        Returns:
            Merged configuration dictionary
        """
        merged = default_config.copy()

        for key, value in custom_config.items():
            if key == "strategy_configs" and isinstance(value, dict):
                # Merge strategy configurations individually
                merged_strategies = merged.get("strategy_configs", {}).copy()
                for strategy_name, strategy_config in value.items():
                    if strategy_name in merged_strategies:
                        # Merge individual strategy config
                        merged_strategies[strategy_name].update(
                            strategy_config
                        )
                    else:
                        # Add new strategy config
                        merged_strategies[strategy_name] = strategy_config
                merged["strategy_configs"] = merged_strategies
            else:
                # Direct override for other keys
                merged[key] = value

        return merged

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix configuration issues.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration dictionary
        """
        # Ensure output directory exists
        output_dir = Path(config.get("output_directory", DATA_CHUNKS_PATH))
        output_dir.mkdir(parents=True, exist_ok=True)
        config["output_directory"] = str(output_dir)

        # Validate enabled strategies
        enabled_strategies = config.get("enabled_strategies", [])
        strategy_configs = config.get("strategy_configs", {})

        # Remove enabled strategies that don't have configuration
        valid_strategies = [
            strategy for strategy in enabled_strategies
            if strategy in strategy_configs
        ]

        if len(valid_strategies) != len(enabled_strategies):
            removed = set(enabled_strategies) - set(valid_strategies)
            logger.warning(
                f"Removed strategies without configuration: {removed}"
            )
            config["enabled_strategies"] = valid_strategies

        # Validate strategy-specific configurations
        for strategy_name, strategy_config in strategy_configs.items():
            config["strategy_configs"][strategy_name] = (
                self._validate_strategy_config(strategy_name, strategy_config)
            )

        return config

    def _validate_strategy_config(
        self,
        strategy_name: str,
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate configuration for a specific strategy.

        Args:
            strategy_name: Name of the strategy
            strategy_config: Configuration for the strategy

        Returns:
            Validated strategy configuration
        """
        validated = strategy_config.copy()

        if strategy_name == "fixed_size":
            # Ensure chunk_size is reasonable
            chunk_size = validated.get("chunk_size", 1000)
            if chunk_size < 100 or chunk_size > 8192:
                logger.warning(
                    f"Fixed size chunk_size {chunk_size} outside recommended "
                    f"range (100-8192), using 1000"
                )
                validated["chunk_size"] = 1000

        elif strategy_name in ["sliding_langchain", "sliding_unstructured"]:
            # Validate overlap settings
            chunk_size = validated.get("chunk_size", 1000)
            chunk_overlap = validated.get("chunk_overlap", 200)

            if chunk_overlap >= chunk_size:
                logger.warning(
                    f"Chunk overlap ({chunk_overlap}) >= chunk size "
                    f"({chunk_size}), adjusting overlap to {chunk_size // 4}"
                )
                validated["chunk_overlap"] = chunk_size // 4

        elif strategy_name == "semantic":
            # Validate size constraints
            min_size = validated.get("min_chunk_size", 200)
            max_size = validated.get("max_chunk_size", 2000)

            if min_size >= max_size:
                logger.warning(
                    f"Semantic min_chunk_size ({min_size}) >= max_chunk_size "
                    f"({max_size}), using defaults"
                )
                validated["min_chunk_size"] = 200
                validated["max_chunk_size"] = 2000

        return validated

    def save_config(self, config: ChunkingConfig, output_path: Path):
        """Save configuration to file.

        Args:
            config: ChunkingConfig object to save
            output_path: Path where to save the configuration
        """
        config_dict = {
            "enabled_strategies": config.enabled_strategies,
            "strategy_configs": config.strategy_configs,
            "output_format": config.output_format,
            "batch_size": config.batch_size,
            "max_workers": config.max_workers,
            "save_intermediate": config.save_intermediate,
            "output_directory": (
                str(config.output_directory)
                if config.output_directory else None
            )
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            if output_path.suffix.lower() in ['.yml', '.yaml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_dict, f, indent=2)

        logger.info(f"Configuration saved to {output_path}")


def get_default_config() -> ChunkingConfig:
    """Get default chunking configuration.

    Returns:
        ChunkingConfig with default settings
    """
    return ChunkingConfig.from_dict(DEFAULT_CHUNKING_CONFIG)


def load_config_from_file(config_path: Path) -> ChunkingConfig:
    """Load configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        ChunkingConfig loaded from file
    """
    manager = ChunkingConfigManager(config_path)
    return manager.load_config()
