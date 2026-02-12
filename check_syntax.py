#!/usr/bin/env python3
"""
Simple syntax check for all Python files in the project.
"""

import os
import py_compile
import sys


def check_syntax(directory):
    """Check syntax of all Python files."""
    errors = []
    checked = 0

    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    py_compile.compile(filepath, doraise=True)
                    checked += 1
                    print(f"✓ {filepath}")
                except py_compile.PyCompileError as e:
                    errors.append((filepath, str(e)))
                    print(f"✗ {filepath}: {e}")

    return checked, errors


if __name__ == "__main__":
    print("检查 Python 文件语法...\n")

    checked, errors = check_syntax("app")

    print(f"\n检查完成: {checked} 个文件")

    if errors:
        print(f"\n发现 {len(errors)} 个错误:")
        for filepath, error in errors:
            print(f"  - {filepath}")
            print(f"    {error}")
        sys.exit(1)
    else:
        print("\n✓ 所有文件语法正确！")
        sys.exit(0)
