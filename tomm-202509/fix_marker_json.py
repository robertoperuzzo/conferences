#!/usr/bin/env python3
"""Fix corrupted marker JSON files by removing image content and keeping only filenames."""

import json
import os
import sys
from pathlib import Path


def fix_marker_json(file_path: str) -> bool:
    """
    Fix a corrupted marker JSON file by removing incomplete image data.

    Args:
        file_path: Path to the corrupted JSON file

    Returns:
        True if successfully fixed, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"Original file size: {len(content):,} characters")

        # Find where the truncation happened - look for incomplete "images" section
        if '"images": {' in content and not content.strip().endswith('}'):
            print("Found incomplete images section, fixing...")

            # Find the start of the images section
            images_start = content.rfind('"images": {')
            if images_start == -1:
                print("Could not find images section start")
                return False

            # Remove everything from the images section onward
            content_before_images = content[:images_start].rstrip()

            # Remove trailing comma if present
            if content_before_images.endswith(','):
                content_before_images = content_before_images[:-1]

            # Add a minimal images section with just filenames (no content)
            # and close the JSON properly
            fixed_content = content_before_images + ',\n    "images": {\n'

            # Look for image references in the original content to preserve filenames
            import re
            image_refs = re.findall(
                r'"(_page_\d+_[^"]+\.(?:jpeg|jpg|png|gif))"', content)

            if image_refs:
                print(
                    f"Found {len(image_refs)} image references: {image_refs}")
                image_entries = []
                for img_ref in image_refs:
                    image_entries.append(
                        f'      "{img_ref}": "image_content_skipped"')

                fixed_content += ',\n'.join(image_entries) + '\n'

            fixed_content += '    }\n}'

            # Validate the fixed JSON
            try:
                data = json.loads(fixed_content)
                print("✅ Fixed JSON is valid")

                # Create backup of original
                backup_path = file_path + '.backup'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Created backup: {backup_path}")

                # Write fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                print(f"Fixed file size: {len(fixed_content):,} characters")
                print(f"Document ID: {data.get('document_id', 'N/A')}")
                print(f"Title: {data.get('title', 'N/A')}")
                print(
                    f"Text length: {len(data.get('full_text', '')):,} characters")
                print(f"Number of elements: {len(data.get('elements', []))}")
                print(f"Number of images: {len(data.get('images', {}))}")

                return True

            except json.JSONDecodeError as e:
                print(f"❌ Fixed JSON is still invalid: {e}")
                return False
        else:
            print("File doesn't appear to have image truncation issue")
            return False

    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return False


def main():
    """Fix all corrupted marker JSON files."""
    marker_dir = Path('/workspace/data/processed/marker')

    if not marker_dir.exists():
        print(f"Marker directory not found: {marker_dir}")
        return

    print("🔧 Fixing corrupted marker JSON files...")
    print("=" * 50)

    fixed_count = 0
    total_count = 0

    for json_file in marker_dir.glob('*.json'):
        print(f"\nProcessing: {json_file.name}")
        total_count += 1

        if fix_marker_json(str(json_file)):
            fixed_count += 1
            print(f"✅ Successfully fixed {json_file.name}")
        else:
            print(f"❌ Could not fix {json_file.name}")

    print("\n" + "=" * 50)
    print(f"Fixed {fixed_count}/{total_count} marker JSON files")


if __name__ == "__main__":
    main()
