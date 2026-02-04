"""Utility functions for chunking strategies.

This module provides common utilities used across different chunking
strategies, including overlap logic, text processing, and metrics calculation.
"""

import re
from typing import List, Dict, Any, Tuple
import logging

from .models import DocumentChunk


logger = logging.getLogger(__name__)


def calculate_overlap_positions(
    elements: List[Dict[str, Any]],
    overlap_percentage: float = 0.2
) -> List[Tuple[int, int]]:
    """Calculate overlap positions for element-based chunking.
    
    Args:
        elements: List of document elements with position information
        overlap_percentage: Percentage of overlap between chunks
        
    Returns:
        List of (start_idx, end_idx) tuples for each chunk
    """
    if not elements or overlap_percentage <= 0:
        return [(0, len(elements))]
    
    chunks = []
    current_start = 0
    
    while current_start < len(elements):
        # Calculate chunk end position
        chunk_end = min(current_start + 10, len(elements))  # Max 10 elements
        
        # Add current chunk
        chunks.append((current_start, chunk_end))
        
        # Calculate next start position with overlap
        if chunk_end >= len(elements):
            break
            
        overlap_elements = max(
            1, int((chunk_end - current_start) * overlap_percentage)
        )
        current_start = chunk_end - overlap_elements
    
    return chunks


def group_elements_by_priority(
    elements: List[Dict[str, Any]],
    priority_elements: List[str] = None
) -> List[List[Dict[str, Any]]]:
    """Group elements by priority for better chunking.
    
    Args:
        elements: List of document elements
        priority_elements: List of element types to prioritize
        
    Returns:
        List of element groups
    """
    if not elements:
        return []
    
    if not priority_elements:
        priority_elements = ["Title", "Header", "NarrativeText"]
    
    groups = []
    current_group = []
    
    for element in elements:
        element_type = element.get('type', 'Unknown')
        
        # Start new group if we hit a high-priority element
        # and current group isn't empty
        if (element_type in priority_elements and
                current_group and
                len(current_group) > 0):
            
            groups.append(current_group)
            current_group = [element]
        else:
            current_group.append(element)
    
    # Add the last group if it's not empty
    if current_group:
        groups.append(current_group)
    
    return groups


def clean_text(text: str) -> str:
    """Clean and normalize text content.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove common PDF artifacts
    text = re.sub(r'\.{3,}', '...', text)  # Multiple dots
    text = re.sub(r'-{2,}', '--', text)    # Multiple dashes
    
    return text


def extract_text_from_elements(elements: List[Dict[str, Any]]) -> str:
    """Extract and combine text from document elements.
    
    Args:
        elements: List of document elements
        
    Returns:
        Combined text from all elements
    """
    if not elements:
        return ""
    
    texts = []
    for element in elements:
        text = element.get('text', '').strip()
        if text:
            texts.append(text)
    
    return '\n\n'.join(texts)


def calculate_text_statistics(text: str) -> Dict[str, Any]:
    """Calculate basic text statistics.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with text statistics
    """
    if not text:
        return {
            'character_count': 0,
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0
        }
    
    # Basic counts
    character_count = len(text)
    word_count = len(text.split())
    
    # Sentence count (rough estimation)
    sentence_endings = re.findall(r'[.!?]+', text)
    sentence_count = len(sentence_endings)
    
    # Paragraph count
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    paragraph_count = len(paragraphs)
    
    return {
        'character_count': character_count,
        'word_count': word_count,
        'sentence_count': sentence_count,
        'paragraph_count': paragraph_count
    }


def validate_chunk_quality(chunk: DocumentChunk) -> Dict[str, Any]:
    """Validate the quality of a generated chunk.
    
    Args:
        chunk: The chunk to validate
        
    Returns:
        Dictionary with quality metrics and issues
    """
    issues = []
    quality_score = 1.0
    
    # Check minimum content length
    if len(chunk.content.strip()) < 50:
        issues.append("Content too short (< 50 characters)")
        quality_score *= 0.5
    
    # Check for sentence boundaries
    content = chunk.content.strip()
    if content and not content[0].isupper():
        issues.append("Doesn't start with capital letter")
        quality_score *= 0.8
    
    if content and content[-1] not in '.!?':
        issues.append("Doesn't end with sentence terminator")
        quality_score *= 0.8
    
    # Check for excessive repetition
    words = content.lower().split()
    if len(words) > 10:
        unique_words = set(words)
        repetition_ratio = len(unique_words) / len(words)
        if repetition_ratio < 0.3:
            issues.append("High word repetition")
            quality_score *= 0.6
    
    # Check token count vs content length consistency
    estimated_tokens = len(words) * 0.75
    if abs(chunk.token_count - estimated_tokens) > (estimated_tokens * 0.5):
        issues.append("Token count seems inconsistent")
        quality_score *= 0.9
    
    return {
        'quality_score': quality_score,
        'issues': issues,
        'character_count': len(content),
        'word_count': len(words),
        'starts_well': content and content[0].isupper(),
        'ends_well': content and content[-1] in '.!?'
    }


def find_sentence_boundaries(text: str, max_length: int) -> List[int]:
    """Find good sentence boundaries for splitting text.
    
    Args:
        text: Text to analyze
        max_length: Maximum desired chunk length
        
    Returns:
        List of character positions where splits can occur
    """
    if not text or max_length <= 0:
        return []
    
    # Find sentence endings
    sentence_endings = []
    for match in re.finditer(r'[.!?]+\s+', text):
        sentence_endings.append(match.end())
    
    if not sentence_endings:
        # Fallback to paragraph breaks
        for match in re.finditer(r'\n\n+', text):
            sentence_endings.append(match.end())
    
    # Select boundaries that are close to max_length
    good_boundaries = []
    for pos in sentence_endings:
        if pos <= len(text):  # Valid position
            good_boundaries.append(pos)
    
    return sorted(good_boundaries)


def optimize_chunk_boundaries(
    text: str, 
    target_size: int, 
    overlap: int = 0
) -> List[Tuple[int, int]]:
    """Optimize chunk boundaries to respect sentence structure.
    
    Args:
        text: Text to chunk
        target_size: Target chunk size in characters
        overlap: Overlap size in characters
        
    Returns:
        List of (start, end) positions for chunks
    """
    if not text:
        return []
    
    boundaries = find_sentence_boundaries(text, target_size)
    if not boundaries:
        # Fallback to simple splitting
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + target_size, len(text))
            chunks.append((start, end))
            start = max(start + target_size - overlap, end)
        return chunks
    
    chunks = []
    start = 0
    
    for boundary in boundaries:
        if boundary - start >= target_size * 0.5:  # Minimum chunk size
            chunks.append((start, boundary))
            start = max(0, boundary - overlap)
    
    # Handle remaining text
    if start < len(text):
        chunks.append((start, len(text)))
    
    return chunks


def merge_small_chunks(
    chunks: List[DocumentChunk], 
    min_size: int = 100
) -> List[DocumentChunk]:
    """Merge chunks that are too small with adjacent chunks.
    
    Args:
        chunks: List of chunks to potentially merge
        min_size: Minimum chunk size threshold
        
    Returns:
        List of chunks with small ones merged
    """
    if not chunks:
        return chunks
    
    merged = []
    i = 0
    
    while i < len(chunks):
        current_chunk = chunks[i]
        
        # If chunk is too small and not the last one, try to merge with next
        if (len(current_chunk.content) < min_size and 
            i + 1 < len(chunks) and
            current_chunk.document_id == chunks[i + 1].document_id):
            
            next_chunk = chunks[i + 1]
            
            # Create merged chunk
            merged_content = current_chunk.content + "\n\n" + next_chunk.content
            merged_chunk = DocumentChunk(
                chunk_id=current_chunk.chunk_id,
                document_id=current_chunk.document_id,
                strategy_name=current_chunk.strategy_name,
                content=merged_content,
                start_position=current_chunk.start_position,
                end_position=next_chunk.end_position,
                token_count=current_chunk.token_count + next_chunk.token_count,
                metadata={
                    **current_chunk.metadata,
                    'merged_from': [current_chunk.chunk_id, next_chunk.chunk_id]
                },
                elements=current_chunk.elements + next_chunk.elements
            )
            
            merged.append(merged_chunk)
            i += 2  # Skip both chunks
        else:
            merged.append(current_chunk)
            i += 1
    
    return merged
