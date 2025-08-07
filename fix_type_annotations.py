#!/usr/bin/env python3
"""
Script to automatically fix common type annotation issues in the codebase.
This addresses the most common ruff errors related to missing type annotations.
"""

import ast
import re
from pathlib import Path
from typing import List, Set


def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the directory."""
    path = Path(directory)
    return list(path.rglob("*.py"))


def add_missing_return_annotations(content: str) -> str:
    """Add missing return type annotations to async functions."""

    # Common patterns for FastAPI endpoints and other functions
    patterns = [
        # FastAPI endpoints returning JSONResponse
        (r'(async def \w+\([^)]*\)):(\s*\n\s*"""[^"]*"""\s*\n.*?return JSONResponse)', r'\1 -> JSONResponse:\2'),
        (r'(async def \w+\([^)]*\)):(\s*\n.*?return JSONResponse)', r'\1 -> JSONResponse:\2'),

        # FastAPI endpoints returning FileResponse
        (r'(async def \w+\([^)]*\)):(\s*\n.*?return FileResponse)', r'\1 -> FileResponse:\2'),

        # WebSocket functions (usually return None)
        (r'(async def websocket_\w+\([^)]*\)):(\s*\n)', r'\1 -> None:\2'),

        # Verify and init methods
        (r'(def verify_\w+\(self\)):(\s*\n)', r'\1 -> None:\2'),
        (r'(def __init__\([^)]*\)):(\s*\n)', r'\1 -> None:\2'),

        # Methods that don't return anything
        (r'(def \w+\(self[^)]*\)):(\s*\n\s*"""[^"]*"""\s*\n(?!.*return))', r'\1 -> None:\2'),

        # Async methods that might return None
        (r'(async def \w+\([^)]*\)):(\s*\n\s*"""[^"]*"""\s*\n(?!.*return))', r'\1 -> None:\2'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

    return content


def fix_import_issues(content: str) -> str:
    """Fix common import issues."""
    
    # Fix type: ignore comments to be more specific
    content = re.sub(r'# type: ignore\[import\]', '# type: ignore[import-untyped]', content)
    
    # Add missing typing imports if type annotations are used
    if ('-> ' in content or ': List[' in content or ': Dict[' in content or ': Optional[' in content) and 'from typing import' not in content:
        # Find the last import line
        lines = content.split('\n')
        last_import_idx = -1
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import_idx = i
        
        if last_import_idx >= 0:
            # Insert typing import after the last import
            typing_imports = []
            if ': List[' in content:
                typing_imports.append('List')
            if ': Dict[' in content:
                typing_imports.append('Dict')
            if ': Optional[' in content:
                typing_imports.append('Optional')
            if ': Any' in content:
                typing_imports.append('Any')
            
            if typing_imports:
                typing_line = f"from typing import {', '.join(sorted(set(typing_imports)))}"
                lines.insert(last_import_idx + 1, typing_line)
                content = '\n'.join(lines)
    
    return content


def fix_common_style_issues(content: str) -> str:
    """Fix common style issues that ruff flags."""
    
    # Fix trailing whitespace
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)
    
    # Fix multiple blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    # Fix missing blank line before class/function definitions
    content = re.sub(r'(\n[^\n]*\n)(class |def |async def )', r'\1\n\2', content)
    
    return content


def process_file(file_path: Path) -> bool:
    """Process a single Python file to fix common issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Skip empty files
        if not original_content.strip():
            return False
        
        content = original_content
        
        # Apply fixes
        content = add_missing_return_annotations(content)
        content = fix_import_issues(content)
        content = fix_common_style_issues(content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"⏭️  No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    print("🔧 Fixing common type annotation and style issues...")
    
    python_files = find_python_files("goldenverba")
    total_files = len(python_files)
    fixed_files = 0
    
    print(f"Found {total_files} Python files to process")
    
    for file_path in python_files:
        if process_file(file_path):
            fixed_files += 1
    
    print(f"\n📊 Summary:")
    print(f"Total files: {total_files}")
    print(f"Files modified: {fixed_files}")
    print(f"Files unchanged: {total_files - fixed_files}")
    
    if fixed_files > 0:
        print(f"\n✅ Fixed common issues in {fixed_files} files!")
        print("Run 'make lint-backend' again to see remaining issues.")
    else:
        print("\n⏭️  No automatic fixes applied.")


if __name__ == "__main__":
    main()
