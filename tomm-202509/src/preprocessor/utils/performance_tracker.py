"""Performance tracking utilities for document extraction.

This module provides performance monitoring capabilities for measuring
extraction speed, memory usage, and other performance metrics.
"""

import time
import psutil
from typing import Dict, Any


class PerformanceTracker:
    """Context manager for tracking performance metrics during extraction.

    This class provides comprehensive performance monitoring including
    processing time, memory usage, and extraction rate calculations.
    """

    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.process = psutil.Process()

    def __enter__(self):
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_metrics(self, text_length: int,
                    pages_processed: int = 1) -> Dict[str, Any]:
        """Calculate performance metrics.

        Args:
            text_length: Number of characters extracted
            pages_processed: Number of pages processed (default: 1)

        Returns:
            Dictionary containing performance metrics
        """
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        processing_time = end_time - self.start_time
        memory_usage = max(end_memory - self.start_memory, 0)

        return {
            "processing_time_seconds": round(processing_time, 3),
            "memory_usage_mb": round(memory_usage, 2),
            "characters_extracted": text_length,
            "pages_processed": pages_processed,
            "extraction_rate": (
                round(text_length / processing_time, 2)
                if processing_time > 0 else 0
            )
        }
