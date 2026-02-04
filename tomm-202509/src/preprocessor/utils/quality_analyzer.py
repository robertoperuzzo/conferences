"""Text quality analysis utilities for document extraction.

This module provides text quality assessment capabilities including
readability analysis, OCR artifact detection, and structure analysis.
"""

import re
from typing import Dict, Any


class QualityAnalyzer:
    """Analyzer for assessing text extraction quality.

    This class provides comprehensive quality metrics for extracted text
    including readability, structure preservation, and OCR artifact detection.
    """

    @staticmethod
    def analyze_text(text: str) -> Dict[str, Any]:
        """Analyze text quality metrics.

        Args:
            text: Extracted text to analyze

        Returns:
            Dictionary containing quality metrics
        """
        if not text:
            return {
                "text_length": 0,
                "word_count": 0,
                "unique_words": 0,
                "readability_score": 0.0,
                "ocr_artifact_count": 0,
                "structure_elements": 0,
                "line_count": 0,
                "average_word_length": 0.0,
                "sentence_count": 0,
                "paragraph_count": 0
            }

        # Basic text statistics
        words = text.split()
        unique_words = set(
            word.lower().strip('.,!?";()[]{}') for word in words
        )
        lines = text.split('\n')
        sentences = re.split(r'[.!?]+', text)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        # OCR artifact detection
        ocr_artifacts = QualityAnalyzer._count_ocr_artifacts(text)

        # Structure elements detection
        structure_elements = QualityAnalyzer._count_structure_elements(text)

        # Readability score (simplified)
        readability_score = QualityAnalyzer._calculate_readability(
            words, sentences
        )

        return {
            "text_length": len(text),
            "word_count": len(words),
            "unique_words": len(unique_words),
            "readability_score": readability_score,
            "ocr_artifact_count": ocr_artifacts,
            "structure_elements": structure_elements,
            "line_count": len(lines),
            "average_word_length": (
                sum(len(word) for word in words) / len(words)
                if words else 0.0
            ),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "paragraph_count": len(paragraphs)
        }

    @staticmethod
    def _count_ocr_artifacts(text: str) -> int:
        """Count potential OCR artifacts in text.

        Args:
            text: Text to analyze

        Returns:
            Number of OCR artifacts detected
        """
        artifact_patterns = [
            r'\b[a-z]\s[a-z]\b',  # Single letter words separated by spaces
            r'[^\w\s]{3,}',       # Multiple special characters together
            r'\b\w{1,2}\s\w{1,2}\b',  # Very short fragmented words
            r'[A-Z]{4,}(?![A-Z])',    # Long sequences of capitals
        ]

        total_artifacts = 0
        for pattern in artifact_patterns:
            matches = re.findall(pattern, text)
            total_artifacts += len(matches)

        return total_artifacts

    @staticmethod
    def _count_structure_elements(text: str) -> int:
        """Count structural elements in text.

        Args:
            text: Text to analyze

        Returns:
            Number of structure elements detected
        """
        structure_patterns = [
            r'^#{1,6}\s',      # Markdown headers
            r'^\*\s',          # Bullet points
            r'^\d+\.\s',       # Numbered lists
            r'^\|\s.*\s\|$',   # Table rows
            r'```',            # Code blocks
            r'\*\*.*\*\*',     # Bold text
            r'\[.*\]\(.*\)',   # Links
        ]

        total_elements = 0
        for pattern in structure_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            total_elements += len(matches)

        return total_elements

    @staticmethod
    def _calculate_readability(words: list, sentences: list) -> float:
        """Calculate a simplified readability score.

        Args:
            words: List of words in the text
            sentences: List of sentences in the text

        Returns:
            Readability score (0-100, higher is more readable)
        """
        if not words or not sentences:
            return 0.0

        # Simplified readability calculation
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Simple formula: penalize long sentences and words
        score = max(0, 100 - (avg_sentence_length * 2) - (avg_word_length * 5))
        return round(score, 2)
