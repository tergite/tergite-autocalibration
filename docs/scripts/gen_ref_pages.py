"""Generate the code reference pages and navigation."""

from pathlib import Path
import mkdocs_gen_files

# Configuration: Files and folders to exclude
EXCLUDE_FILES = {
    "__init__.py",
    "__main__.py",
    "test.py",  # Exclude test files
    "test_*.py",  # Exclude test files
    "*_test.py",  # Exclude test files (alternative naming)
    "conftest.py",  # Exclude pytest configuration
    "setup.py",  # Exclude setup files
    "config.py",  # Example: exclude config files
}

EXCLUDE_FOLDERS = {
    "tests",  # Exclude test directories
    "templates",  # Exclude test directories
    "experimental",  # Exclude test directories
    "__pycache__",  # Exclude Python cache
    ".pytest_cache",  # Exclude pytest cache
    "migrations",  # Example: exclude database migrations
    "scripts",  # Example: exclude utility scripts
}

EXCLUDE_PATTERNS = {
    "*/tests/*",  # Exclude anything in tests folders
    "*/test_*",  # Exclude test files in any folder
    "*/__pycache__/*",  # Exclude cache files
    "*/migrations/*",  # Exclude migration files
}


def should_exclude_path(path: Path, src: Path) -> bool:
    """Check if a path should be excluded based on configuration."""
    relative_path = path.relative_to(src)

    # Check if filename matches any exclude pattern
    filename = path.name
    for pattern in EXCLUDE_FILES:
        if pattern.startswith("*") and pattern.endswith("*"):
            # Pattern like "*test*"
            if pattern[1:-1] in filename:
                return True
        elif pattern.startswith("*"):
            # Pattern like "*.py" or "*_test.py"
            if filename.endswith(pattern[1:]):
                return True
        elif pattern.endswith("*"):
            # Pattern like "test_*"
            if filename.startswith(pattern[:-1]):
                return True
        else:
            # Exact match
            if filename == pattern:
                return True

    # Check if any parent folder should be excluded
    for part in relative_path.parents:
        if part.name in EXCLUDE_FOLDERS:
            return True

    # Check if the file's immediate parent is excluded
    if relative_path.parent.name in EXCLUDE_FOLDERS:
        return True

    # Check pattern-based exclusions
    path_str = relative_path.as_posix()
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*/") and pattern.endswith("/*"):
            # Pattern like "*/tests/*"
            folder_name = pattern[2:-2]
            if f"/{folder_name}/" in f"/{path_str}/":
                return True
        elif pattern.startswith("*/"):
            # Pattern like "*/test_*"
            if path_str.endswith(pattern[2:]) or ("/" + pattern[2:]) in path_str:
                return True

    return False


# Create a Nav object to build navigation structure for the reference docs
nav = mkdocs_gen_files.Nav()

# Define the root of the project (two levels up from this script)
root = Path(__file__).parent.parent.parent

# Define the source directory of the package you want to document
src = root / "tergite_autocalibration"

# Walk through all Python files in the package
for path in sorted(src.rglob("*.py")):
    # Skip excluded files and folders
    if should_exclude_path(path, src):
        continue

    # Compute the module path relative to the package, without .py extension
    module_path = path.relative_to(src).with_suffix("")

    # Compute the documentation path (e.g. foo/bar.py -> foo/bar.md)
    doc_path = path.relative_to(src).with_suffix(".md")

    # Full path to the output documentation file, under reference/
    full_doc_path = Path("reference", doc_path)

    # Break the module path into parts (e.g., foo/bar.py -> ("foo", "bar"))
    parts = tuple(module_path.parts)

    # Skip __init__.py and __main__.py — they don't need separate doc pages
    # (This is now handled by the exclusion logic above, but kept for explicit clarity)
    if parts[-1] in {"__init__", "__main__"}:
        continue

    # Add this module to the navigation structure
    nav[parts] = doc_path.as_posix()

    # Write the API documentation stub using mkdocstrings syntax
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(
            ("tergite_autocalibration", *parts)
        )  # e.g., chalmers_qubit.foo.bar
        fd.write(f"::: {ident}\n")  # Tell mkdocstrings to document this object

    # Set the "Edit this page" link to point to the source code location
    mkdocs_gen_files.set_edit_path(full_doc_path, Path("../") / path)

# Generate the SUMMARY.md file for the reference section, which defines the nav structure
with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
