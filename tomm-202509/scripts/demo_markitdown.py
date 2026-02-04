#!/usr/bin/env python3
"""
MarkItDown Integration Demo - ADR-011

This script demonstrates the new MarkItDown extractor capabilities
for multi-format document processing.
"""

from src.preprocessor import DocumentPreprocessor
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_test_files():
    """Create sample files to demonstrate MarkItDown capabilities."""
    test_files = []

    # Create a test Markdown file
    md_content = """# MarkItDown Test Document

This is a **demonstration** of MarkItDown's capabilities.

## Features

- Multi-format document processing
- LLM-optimized output
- Support for Office documents
- Image and media processing

### Code Example

```python
from src.preprocessor import DocumentPreprocessor
dp = DocumentPreprocessor()
result = dp.extract_text_from_file("document.docx", method="markitdown")
```

> MarkItDown excels at converting various document formats to clean Markdown.
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(md_content)
        test_files.append(Path(f.name))

    # Create a test HTML file
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test HTML Document</title>
</head>
<body>
    <h1>HTML Document Test</h1>
    <p>This HTML file demonstrates MarkItDown's ability to process web content.</p>
    <ul>
        <li>Convert HTML to clean Markdown</li>
        <li>Preserve structure and formatting</li>
        <li>Remove unnecessary markup</li>
    </ul>
    <blockquote>
        MarkItDown creates LLM-friendly output from web content.
    </blockquote>
</body>
</html>"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        test_files.append(Path(f.name))

    return test_files


def main():
    """Demonstrate MarkItDown extraction capabilities."""
    print("MarkItDown Integration Demo - ADR-011")
    print("=" * 45)

    # Initialize preprocessor
    preprocessor = DocumentPreprocessor()

    print(f"Available methods: {preprocessor.SUPPORTED_METHODS}")
    print(
        f"MarkItDown enabled: {'markitdown' in preprocessor.SUPPORTED_METHODS}")

    # Create test files
    print("\nCreating test files...")
    test_files = create_test_files()

    try:
        for test_file in test_files:
            print(f"\n{'-' * 50}")
            print(f"Processing: {test_file.name}")
            print(f"Format: {test_file.suffix}")
            print(f"{'-' * 50}")

            # Test direct MarkItDown extraction
            try:
                result = preprocessor.extract_text_from_file(
                    test_file, method="markitdown"
                )
                print("✅ MarkItDown extraction successful!")
                print(f"   Text length: {len(result.text):,} characters")
                print(
                    f"   Method used: {result.method_specific_data.get('extraction_method')}")
                print(
                    f"   File format: {result.method_specific_data.get('file_format')}")

                # Show first 200 chars of extracted text
                preview = result.text[:200].replace('\n', ' ')
                print(f"   Preview: {preview}...")

            except Exception as e:
                print(f"❌ MarkItDown extraction failed: {e}")

            # Test auto-detection
            try:
                auto_result = preprocessor.extract_text_from_file(
                    test_file, method="auto"
                )
                auto_method = auto_result.method_specific_data.get(
                    'extraction_method')
                print(f"✅ Auto-detection selected: {auto_method}")

            except Exception as e:
                print(f"❌ Auto-detection failed: {e}")

    finally:
        # Clean up test files
        for test_file in test_files:
            test_file.unlink()

    print(f"\n{'=' * 45}")
    print("MarkItDown Demo Complete!")
    print("\nSupported formats:")
    print("- Office documents (.docx, .xlsx, .pptx)")
    print("- Web content (.html, .htm)")
    print("- Markdown (.md)")
    print("- Images (.jpg, .png, etc.)")
    print("- Audio/Video files")
    print("- PDF files")
    print("- And many more!")


if __name__ == "__main__":
    main()
