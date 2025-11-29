#!/usr/bin/env python3
"""
Script to automatically fix common pylint issues
"""
import re

def fix_file(filepath):
    """Fix pylint issues in vendor_monitor.py"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Fix 1: Add encoding='utf-8' to open() calls
    content = re.sub(
        r"open\(([^)]+)\)(\s+as\s+)",
        r"open(\1, encoding='utf-8')\2",
        content
    )

    # Fix 2: Convert logger.info(f"...") to logger.info("...", ...)
    # This is complex, so we'll do it manually for key patterns

    # Fix 3: Remove f-strings without interpolation
    content = re.sub(r'logger\.info\(f"([^"]*?)"\)', r'logger.info("\1")', content)
    content = re.sub(r'logger\.warning\(f"([^"]*?)"\)', r'logger.warning("\1")', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed pylint issues")
    else:
        print("No changes needed")

if __name__ == '__main__':
    fix_file('vendor_monitor.py')
