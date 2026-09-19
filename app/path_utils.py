"""
Robust Project Path Utilities
-----------------------------
Provides dynamic root finding and candidate file resolution to eliminate hardcoded
relative directory depths (e.g., .parent.parent.parent).
"""

from pathlib import Path
import os
import sys

def find_project_root(file_origin=None) -> Path:
    """
    Dynamically locates the workspace root directory by searching upwards for root marker files.
    """
    if file_origin is None:
        file_origin = __file__
    
    origin_path = Path(file_origin).resolve()
    # Check current directory and all parent directories
    for parent in [origin_path] + list(origin_path.parents):
        if (
            (parent / "pytest.ini").exists()
            or (parent / ".git").exists()
            or (parent / "Dockerfile").exists()
            or (parent / "README.md").exists()
            or (parent / "requirements.txt").exists()
        ):
            return parent
            
    # Fallback default: 2 levels up from app/path_utils.py
    return Path(__file__).resolve().parent.parent

def resolve_path(relative_path_str: str, file_origin=None) -> Path:
    """
    Resolves a relative path string against the project root.
    If the target does not exist at project_root / relative_path_str,
    it searches common candidate locations before returning default target.
    """
    root = find_project_root(file_origin)
    target = root / relative_path_str
    
    if target.exists():
        return target
        
    # Search fallback candidate locations
    candidates = [
        root / relative_path_str,
        root / "data" / "processed" / Path(relative_path_str).name,
        root / "data" / "raw" / Path(relative_path_str).name,
        root / "data" / "audit" / Path(relative_path_str).name,
        root / "docs" / "reports" / Path(relative_path_str).name,
        root / "docs" / "ab_testing" / Path(relative_path_str).name,
        root / "models" / Path(relative_path_str).name,
    ]
    
    for candidate in candidates:
        if candidate.exists():
            return candidate
            
    return target

def ensure_sys_path():
    """Ensures app/ directory and project root are in sys.path for seamless imports."""
    root = find_project_root()
    app_dir = root / "app"
    for p in [str(root), str(app_dir)]:
        if p not in sys.path:
            sys.path.insert(0, p)

# Auto-execute path registration on import
ensure_sys_path()
