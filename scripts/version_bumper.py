import argparse
from pathlib import Path
from typing import List, Optional
import re
import requests

RAW_VERSION_RE = re.compile(r'(?P<package>.*)\s*=\s*\"(?P<version>[\^\~\>\=\<\!]?[\d\.\-\w]+)\"')
EXPANDED_VER_RE = re.compile(
    r'(?P<package>.*)\s*=\s*\{(.*)version\s*=\s*\"(?P<version>[\^\~\>\=\<\!]?[\d\.\-\w]+)\"(.*)\}'
)

def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed command line arguments.

    Raises:
        None

    Examples:
        >>> parse_args()
        Namespace(file=Path(''), section='tool.poetry.dependencies')

    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=Path,
    )
    parser.add_argument(
        "--section",
        "-s",
        type=str,
        default="tool.poetry.dependencies",
    )
    output = parser.parse_args()
    if output is None:
        return None
    return output

def get_dependencies(path: Path, section: str) -> List[str]:
    """
    Get the dependencies for a given path and section.

    Args:
        path (Path): The path to the file or directory.
        section (str): The section of the file or directory.

    Returns:
        List[str]: A list of dependencies for the given path and section.

    Raises:
        None: No exceptions are raised.

    Example:
        >>> path = Path('/path/to/file')
        >>> section = 'main'
        >>> get_dependencies(path, section)
        None
    """

    return None

def get_new_version(package_name: str) -> Optional[str]:
    """
    This function retrieves the latest version of a given package from the PyPI repository.

    Args:
        package_name (str): The name of the package to retrieve the latest version for.

    Returns:
        Optional[str]: The latest version of the package, or None if an error occurred.

    Raises:
        None: This function does not raise any exceptions.

    Example:
        >>> get_new_version("requests")
        '2.26.0'
    """

    resp = requests.get(f'https://pypi.org/pypi/{package_name}/json')
    if not resp.ok:
        return None
    rjson = resp.json()
    return rjson['info']["version"]


def bump_version(dependency: str) -> str:
    """
    This function is used to bump the version of a dependency in a given string.

    Args:
        dependency (str): The string representation of the dependency.

    Returns:
        str: The updated string with the bumped version, or None if no update is needed.

    Raises:
        None

    Example:
        >>> bump_version("^requests==2.25.0")
        Checking requests
        Found new version: 2.26.0
        '^requests==2.26.0'

    Note:
        - The function expects the dependency string to be in a specific format.
        - The function uses regular expressions to extract the package name and version.
        - The function calls the 'get_new_version' function to retrieve the latest version of the package.
    """

    exp_match = EXPANDED_VER_RE.match(dependency)
    raw_match = None
    if exp_match:
        package = exp_match.group("package").strip()
        version = exp_match.group("version").lstrip("^=!~<>")
    else:
        raw_match = RAW_VERSION_RE.match(dependency)
    if raw_match:
        package = raw_match.group("package").strip()
        version = raw_match.group("version").lstrip("^=!~<>")
    if exp_match is None and raw_match is None:
        return None

    print(f"Checking {package}")
    new_version = get_new_version(package)
    if new_version is not None and version != new_version:
        print(f"Found new version: {new_version}")
        return dependency.replace(version, new_version)

    return None

def main():
    """
    Main function to update dependencies in a file.

    Args:
        file (str): The path to the file containing the dependencies.
        section (str): The section of the file where the dependencies are located.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the specified section does not exist in the file.

    Example:
        >>> args = parse_args()
        >>> deps = get_dependencies(args.file, args.section)
        >>> lines = args.file.read_text().splitlines(keepends=False)
        >>> for i, dep in deps:
        ...     new_version = bump_version(dep)
        ...     if new_version:
        ...         lines[i] = new_version
        >>> args.file.write_text("\n".join(lines))
    """

    args = parse_args()
    deps = get_dependencies(args.file, args.section)
    lines = args.file.read_text().splitlines(keepends=False)
    for i, dep in deps:
        new_version = bump_version(dep)
        if new_version:
            lines[i] = new_version
    args.file.write_text("\n".join(lines))
    


if __name__ == "__main__":
    main()
