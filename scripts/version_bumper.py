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
        None: No exceptions are raised.

    Example:
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
    This function retrieves the dependencies from a given file path and section.

    Args:
        path (Path): The path to the file.
        section (str): The section to retrieve the dependencies from.

    Returns:
        List[str]: A list of dependencies.

    Raises:
        None: This function does not raise any exceptions.

    Example:
        >>> path = Path('path/to/file')
        >>> section = 'dependencies'
        >>> get_dependencies(path, section)
        [(0, 'dependency1'), (1, 'dependency2'), ...]

    Note:
        - This function assumes that the file is in a specific format where dependencies are listed under sections.
        - The function ignores lines starting with '[' that do not match the specified section.
        - The function ignores lines starting with 'python =' and '{%'.
    """

    read_file = path.read_text()
    recording = False
    deps = []
    for index, line in enumerate(read_file.splitlines(keepends=False)):
        if line.startswith('[') and line.strip('[]') != section:
            recording = False
            continue
        if line == f"[{section}]":
            recording = True
            continue
        if line.startswith('python ='):
            continue
        if line.startswith('{%'):
            continue
        if recording:
            deps.append((index, line))
    return deps

def get_new_version(package_name: str) -> Optional[str]:
    """
    This function retrieves the latest version of a given package from the PyPI repository.

    Args:
        package_name (str): The name of the package to retrieve the latest version for.

    Returns:
        Optional[str]: The latest version of the package, or None if the request fails.

    Raises:
        None

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

    Parameters:
    - dependency (str): The string representation of the dependency.

    Returns:
    - str: The updated string with the bumped version.

    Exceptions:
    - None

    Example:
    ```python
    dependency = "package==1.0.0"
    bumped_version = bump_version(dependency)
    print(bumped_version)  # Output: "package==2.0.0"
    ```
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

    :param args: Command line arguments parsed using `parse_args()`.
    :type args: argparse.Namespace
    :raises FileNotFoundError: If the specified file is not found.
    :raises ValueError: If the specified section is not found in the file.
    :returns: None
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
