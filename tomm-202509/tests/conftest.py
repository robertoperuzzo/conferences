"""Pytest configuration and shared fixtures for preprocessing tests."""

import tempfile
from pathlib import Path
import pytest
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create subdirectories
        raw_dir = temp_path / "raw"
        processed_dir = temp_path / "processed"
        raw_dir.mkdir(exist_ok=True)
        processed_dir.mkdir(exist_ok=True)
        
        yield {
            'base': temp_path,
            'raw': raw_dir,
            'processed': processed_dir
        }


@pytest.fixture
def sample_paper():
    """Sample paper data for testing."""
    return {
        'paper_id': 'test.2023.001',
        'title': 'A Test Paper on Natural Language Processing',
        'abstract': 'This paper presents a comprehensive study of test methodologies in NLP research.',
        'authors': ['Test Author', 'Another Author', 'Third Author'],
        'categories': ['cs.CL', 'cs.AI'],
        'content': '''Abstract
This paper presents a comprehensive study of test methodologies in NLP research.
We propose novel approaches to testing and validation in machine learning systems.

1 Introduction
Natural language processing has become increasingly important in recent years.
This introduction provides background on the field and motivation for our work.

The rest of this paper is organized as follows. Section 2 describes our methodology.
Section 3 presents experimental results. Section 4 concludes the paper.

2 Methodology
Our methodology combines traditional statistical approaches with modern machine learning.
We use a multi-step process to ensure robust and reliable results.

First, we collect and preprocess our data using standard techniques.
Second, we apply our novel testing framework to validate the results.

3 Results
Our experiments demonstrate significant improvements over baseline methods.
Table 1 shows the performance metrics across different test configurations.

The results indicate that our approach is both effective and efficient.
We achieve state-of-the-art performance on multiple benchmark datasets.

4 Conclusion
This work presents a novel testing framework for NLP research.
Future work will extend these methods to additional domains and applications.'''
    }


@pytest.fixture
def multiple_sample_papers(sample_paper):
    """Generate multiple sample papers for testing."""
    papers = []
    for i in range(3):
        paper = sample_paper.copy()
        paper['paper_id'] = f'test.2023.{i+1:03d}'
        paper['title'] = f'{paper["title"]} - Part {i+1}'
        papers.append(paper)
    return papers


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
