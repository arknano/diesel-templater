"""
Diesel Templater - HTML template processor.

Processes HTML files with template markers (%template_name%) and generates
static output files with static assets.

Usage:
    python diesel.py <path_to_config_file> [export_dir]

Example:
    python diesel.py diesel.config
    python diesel.py /path/to/project/diesel.config ./dist
"""

import os
import sys
import shutil
import re
import json
import fnmatch
import argparse
from typing import Dict, Any, Optional


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXPORT_DIR = os.path.join(SCRIPT_DIR, 'export')


# Default configuration. File exclusions may be filenames, relative paths, or glob patterns.
DEFAULT_CONFIG = {
    'template_dir': 'site/templates',
    'source_dir': 'site',
    'template_pattern': r'%(\w+)%',
    'exclude_dirs': ['templates'],
    'exclude_files': []
}


def load_config(config_path: str, export_dir: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a JSON config file."""
    config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config_dir = os.path.dirname(config_path)

    try:
        with open(config_path, 'r') as f:
            user_config = json.load(f)
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON in config file: {e}")

    # Merge with defaults
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    config['export_dir'] = export_dir or DEFAULT_EXPORT_DIR

    # Convert relative paths to absolute
    for key in ['template_dir', 'source_dir']:
        if key in config:
            path = config[key]
            if not os.path.isabs(path):
                config[key] = os.path.join(config_dir, path)
            else:
                config[key] = os.path.abspath(path)

    config['export_dir'] = os.path.abspath(config['export_dir'])
    config['base_dir'] = config_dir
    return config


def ensure_export_dir(export_dir: str) -> str:
    """Create export directory if it doesn't exist."""
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    return export_dir


def is_same_or_nested_path(path_a: str, path_b: str) -> bool:
    """Return whether two paths are equal or one is nested inside the other."""
    abs_a = os.path.abspath(path_a)
    abs_b = os.path.abspath(path_b)
    try:
        common_path = os.path.commonpath([abs_a, abs_b])
    except ValueError:
        return False
    return common_path in (abs_a, abs_b)


def is_same_or_parent_path(parent_path: str, child_path: str) -> bool:
    """Return whether parent_path is equal to or contains child_path."""
    abs_parent = os.path.abspath(parent_path)
    abs_child = os.path.abspath(child_path)
    try:
        return os.path.commonpath([abs_parent, abs_child]) == abs_parent
    except ValueError:
        return False


def validate_export_dir(config: Dict[str, Any]) -> None:
    """Prevent cleaning paths that overlap with source or config directories."""
    export_dir = config['export_dir']

    if is_same_or_nested_path(export_dir, config['source_dir']):
        raise ValueError(
            f"Export directory must not overlap with source_dir: {config['source_dir']}"
        )

    if is_same_or_parent_path(export_dir, config['base_dir']):
        raise ValueError(
            f"Export directory must not contain the config directory: {config['base_dir']}"
        )


def adjust_relative_paths(content: str, file_rel_path: str) -> str:
    """
    Adjust relative paths in content based on the file's location.

    For files in subdirectories, adds appropriate ../ prefixes to relative paths.
    Leaves absolute URLs, anchors, and already-adjusted paths unchanged.
    """
    if not file_rel_path or file_rel_path == '.':
        return content

    # Calculate directory depth
    depth = len(file_rel_path.split(os.sep)) - 1
    if depth == 0:
        return content

    prefix = '../' * depth

    def adjust_path(match):
        attr_name = match.group(1)  # href= or src=
        quote = match.group(2)      # opening quote
        path = match.group(3)       # the path
        closing_quote = match.group(4)  # closing quote

        # Skip absolute URLs, anchors, and already-adjusted paths
        if (path.startswith(('http://', 'https://', 'mailto:', '#', '/')) or
            path.startswith('../')):
            return match.group(0)

        return f'{attr_name}{quote}{prefix}{path}{closing_quote}'

    # Match href/src attributes with quotes
    pattern = r'((?:href|src)=)(["\'])([^"\']+)(["\'])'
    return re.sub(pattern, adjust_path, content, flags=re.IGNORECASE)


def process_templates(content: str, template_dir: str, template_pattern: str, file_rel_path: str = "") -> str:
    """
    Replace template markers with template file contents.

    Adjusts relative paths in template content based on file location.
    """
    template_regex = re.compile(template_pattern)

    def replace_template(match: re.Match) -> str:
        template_name = match.group(1)
        template_file = os.path.join(template_dir, f"{template_name}.html")

        if os.path.exists(template_file):
            with open(template_file, 'r') as f:
                template_content = f.read()

            return adjust_relative_paths(template_content, file_rel_path)

        print(f"Warning: Template '{template_name}' not found at {template_file}")
        return match.group(0)

    return template_regex.sub(replace_template, content)


def is_excluded_file(file_name: str, rel_path: str, exclude_files: list) -> bool:
    """Return whether a file matches an exclude_files entry."""
    normalized_rel_path = rel_path.replace(os.sep, '/')

    for excluded_file in exclude_files:
        normalized_excluded = str(excluded_file).replace(os.sep, '/')
        if (
            file_name == normalized_excluded or
            normalized_rel_path == normalized_excluded or
            fnmatch.fnmatch(file_name, normalized_excluded) or
            fnmatch.fnmatch(normalized_rel_path, normalized_excluded)
        ):
            return True

    return False


def copy_site_files(source_dir: str, export_dir: str, exclude_dirs: list, exclude_files: list) -> None:
    """Copy files from source to export, skipping configured directories and files."""
    for root, dirs, files in os.walk(source_dir):
        # Prevent os.walk from descending into excluded directories.
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            source_path = os.path.join(root, file)
            rel_path = os.path.relpath(source_path, source_dir)

            # Match exclude_files against both the basename and source-relative path.
            if is_excluded_file(file, rel_path, exclude_files):
                continue

            export_path = os.path.join(export_dir, rel_path)

            # Ensure destination directory exists
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            shutil.copy2(source_path, export_path)


def process_html_files(config: Dict[str, Any]) -> None:
    """Process all HTML files in export directory, replacing templates and adjusting paths."""
    export_dir = config['export_dir']
    template_dir = config['template_dir']
    template_pattern = config.get('template_pattern', r'%(\w+)%')

    # Find all HTML files
    html_files = []
    for root, dirs, files in os.walk(export_dir):
        html_files.extend(os.path.join(root, f) for f in files if f.endswith('.html'))

    for filepath in html_files:
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            rel_path = os.path.relpath(filepath, export_dir)
            processed_content = process_templates(content, template_dir, template_pattern, rel_path)

            with open(filepath, 'w') as f:
                f.write(processed_content)

            print(f"Successfully processed {rel_path}")

        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Build a static HTML site from reusable template snippets."
    )
    parser.add_argument(
        'config',
        help="Path to the JSON config file.",
    )
    parser.add_argument(
        'export_dir',
        nargs='?',
        default=DEFAULT_EXPORT_DIR,
        help="Output directory. Defaults to export/ next to diesel.py.",
    )
    return parser.parse_args()


def main() -> None:
    """Main build function."""
    args = parse_args()

    try:
        config = load_config(args.config, os.path.abspath(args.export_dir))
        validate_export_dir(config)

        print(f"Loaded config from: {args.config}")
        print(f"Working directory: {config['base_dir']}")
        print(f"Export directory: {config['export_dir']}")
        print()

        export_dir = config['export_dir']
        source_dir = config['source_dir']
        exclude_dirs = config.get('exclude_dirs', ['templates'])
        exclude_files = config.get('exclude_files', [])

        # Clean and create export directory
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
        ensure_export_dir(export_dir)

        # Copy all site files
        print("Copying site files...")
        copy_site_files(source_dir, export_dir, exclude_dirs, exclude_files)

        # Process templates
        print("\nProcessing templates...")
        process_html_files(config)

        print("\nBuild completed successfully!")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
