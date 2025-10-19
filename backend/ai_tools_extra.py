"""
AI Dev Tools - Advanced Search and Analysis
Provides file listing, grep search, and AST outline for Python files
READ-ONLY - No file modifications
"""

import os
import re
import ast
from typing import List, Dict, Any

# Ignore common build/dependency directories
IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "dist", "build", "out",
    ".next", ".turbo", "coverage", "__pycache__", ".pytest_cache",
    ".mypy_cache", "venv", "env"
}

# Ignore binary/media file extensions
IGNORE_EXT = {
    ".png", ".jpg", ".jpeg", ".pdf", ".ico", ".lock",
    ".map", ".svg", ".gif", ".webp", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".mp3", ".avi"
}


def _get_repo_roots() -> List[str]:
    """Get repository roots from environment"""
    repo_root = os.getenv("REPO_ROOT", "/app/backend,/app/frontend")
    return [r.strip() for r in repo_root.split(",")]


def _is_skippable_dir(dirpath: str) -> bool:
    """Check if directory should be skipped"""
    parts = dirpath.split(os.sep)
    return any(seg in IGNORE_DIRS for seg in parts)


def _is_text_file(path: str) -> bool:
    """Check if file is text (not binary/media)"""
    _, ext = os.path.splitext(path)
    return ext.lower() not in IGNORE_EXT


def _get_relative_path(abs_path: str, root: str) -> str:
    """Get relative path from root"""
    root_name = os.path.basename(root.rstrip("/"))
    rel_path = os.path.relpath(abs_path, root)
    return os.path.join(root_name, rel_path)


async def list_files(prefix: str = "") -> List[str]:
    """
    List all text files in repository roots
    
    Args:
        prefix: Filter files by path prefix
        
    Returns:
        List of relative file paths
    """
    files = []
    
    for root in _get_repo_roots():
        if not os.path.exists(root):
            continue
            
        for dirpath, _, filenames in os.walk(root):
            if _is_skippable_dir(dirpath):
                continue
                
            for filename in filenames:
                abs_path = os.path.join(dirpath, filename)
                
                if not _is_text_file(abs_path):
                    continue
                
                rel_path = _get_relative_path(abs_path, root)
                
                if prefix and prefix not in rel_path:
                    continue
                
                files.append(rel_path)
    
    return sorted(files)


async def grep(pattern: str, path_prefix: str = "") -> List[Dict[str, Any]]:
    """
    Search for pattern in files (grep-like)
    
    Args:
        pattern: Regex pattern to search
        path_prefix: Filter files by path prefix
        
    Returns:
        List of matches with path, line number, and text
    """
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return [{"error": f"Invalid regex: {str(e)}"}]
    
    hits = []
    
    for root in _get_repo_roots():
        if not os.path.exists(root):
            continue
            
        for dirpath, _, filenames in os.walk(root):
            if _is_skippable_dir(dirpath):
                continue
                
            for filename in filenames:
                abs_path = os.path.join(dirpath, filename)
                
                if not _is_text_file(abs_path):
                    continue
                
                rel_path = _get_relative_path(abs_path, root)
                
                if path_prefix and not rel_path.startswith(path_prefix):
                    continue
                
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                hits.append({
                                    "path": rel_path,
                                    "line": line_num,
                                    "text": line.rstrip()[:300]  # Truncate long lines
                                })
                                
                                # Limit hits per file
                                if len([h for h in hits if h["path"] == rel_path]) >= 10:
                                    break
                except Exception:
                    # Skip files that can't be read
                    pass
    
    return hits[:100]  # Limit total results


async def ast_outline_py(path: str) -> List[Dict[str, Any]]:
    """
    Get AST outline of Python file (classes and functions)
    
    Args:
        path: Relative path to Python file
        
    Returns:
        List of functions and classes with line numbers
    """
    # Security: Validate and resolve path safely
    roots = _get_repo_roots()
    
    # Try each root
    for root in roots:
        # Extract relative part (remove root name prefix)
        parts = path.split("/", 1)
        if len(parts) > 1:
            rel_path = parts[1]
        else:
            rel_path = path
        
        safe_abs = os.path.normpath(os.path.join(root, rel_path))
        
        # Ensure path is within root
        if not safe_abs.startswith(os.path.normpath(root)):
            continue
        
        if not os.path.exists(safe_abs):
            continue
        
        if not safe_abs.endswith(".py"):
            return [{"error": "Not a Python file"}]
        
        try:
            with open(safe_abs, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            
            tree = ast.parse(source)
            outline = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get docstring if available
                    docstring = ast.get_docstring(node)
                    outline.append({
                        "type": "function",
                        "name": node.name,
                        "lineno": node.lineno,
                        "docstring": docstring[:100] if docstring else None
                    })
                elif isinstance(node, ast.AsyncFunctionDef):
                    docstring = ast.get_docstring(node)
                    outline.append({
                        "type": "async_function",
                        "name": node.name,
                        "lineno": node.lineno,
                        "docstring": docstring[:100] if docstring else None
                    })
                elif isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    outline.append({
                        "type": "class",
                        "name": node.name,
                        "lineno": node.lineno,
                        "docstring": docstring[:100] if docstring else None
                    })
            
            return sorted(outline, key=lambda x: x["lineno"])
        
        except SyntaxError as e:
            return [{"error": f"Syntax error: {str(e)}"}]
        except Exception as e:
            return [{"error": f"Failed to parse: {str(e)}"}]
    
    return [{"error": "File not found in repository roots"}]
