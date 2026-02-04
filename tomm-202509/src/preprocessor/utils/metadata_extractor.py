"""Metadata extraction utilities for document processing.

This module provides utilities for extracting metadata from filenames,
document properties, and other sources.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class MetadataExtractor:
    """Utility for extracting metadata from documents and filenames.

    This class provides standardized metadata extraction capabilities
    including filename parsing, document ID generation, and timestamp handling.
    """

    @staticmethod
    def extract_metadata_from_filename(file_path: Path) -> Dict[str, Any]:
        """Extract metadata from filename using common patterns.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            "original_filename": file_path.name,
            "file_extension": file_path.suffix.lower(),
            "file_size_bytes": (
                file_path.stat().st_size if file_path.exists() else 0
            ),
            "creation_date": datetime.now().isoformat(),
            "document_id": None,
            "title": None,
            "authors": [],
            "year": None,
            "version": None,
            "language": "unknown"
        }

        filename_stem = file_path.stem

        # Try to extract document ID (ArXiv pattern: YYMMDDXX_Title)
        arxiv_match = re.match(r'^(\d{7,8})_(.+)$', filename_stem)
        if arxiv_match:
            metadata["document_id"] = arxiv_match.group(1)
            metadata["title"] = arxiv_match.group(2).replace('_', ' ')

        # Try to extract year from filename
        year_match = re.search(r'(19|20)\d{2}', filename_stem)
        if year_match:
            metadata["year"] = int(year_match.group())

        # Try to extract version
        version_match = re.search(r'v(\d+)', filename_stem, re.IGNORECASE)
        if version_match:
            metadata["version"] = version_match.group(1)

        # Extract title if not already found
        if not metadata["title"]:
            # Remove common patterns and clean up
            clean_title = re.sub(r'[\d\-_]+', ' ', filename_stem)
            clean_title = re.sub(r'\s+', ' ', clean_title).strip()
            if clean_title:
                metadata["title"] = clean_title

        return metadata

    @staticmethod
    def generate_document_id(file_path: Path) -> str:
        """Generate document ID from filename for matching processed files.

        Args:
            file_path: Path to the original file

        Returns:
            Document ID string used as prefix for processed files
        """
        # Convert original filename, preserve underscores, remove others
        original_name = file_path.stem.replace(' ', '_')
        clean_name = re.sub(r'[^a-z0-9_]', '', original_name.lower())
        return clean_name

    @staticmethod
    def generate_output_filename(file_path: Path,
                                 method: str = "",
                                 include_timestamp: bool = True) -> str:
        """Generate output filename based on original file and method.

        Args:
            file_path: Original file path
            method: Extraction method name
            include_timestamp: Whether to include timestamp

        Returns:
            Generated output filename
        """
        # Get clean document ID
        doc_id = MetadataExtractor.generate_document_id(file_path)

        # Build filename parts
        parts = [doc_id]

        if method:
            parts.append(method)

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            parts.append(timestamp)

        return "_".join(parts) + ".json"
