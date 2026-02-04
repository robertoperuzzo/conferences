"""ArXiv downloader module for the chunking strategies demo.

This module provides functionality to download ArXiv papers based on
search queries and categories, as specified in the Demo Implementation Plan.
"""

from .arxiv_downloader import (
    ArxivDownloader,
    download_papers_by_category,
    download_papers_by_query
)

__all__ = [
    'ArxivDownloader',
    'download_papers_by_category',
    'download_papers_by_query'
]
