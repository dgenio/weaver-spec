"""
Contract version constants and compatibility helpers.
"""

# The current contract version. Must match pyproject.toml [project] version.
CONTRACT_VERSION = "0.2.0"

# The JSON Schema $id version prefix (corresponds to MAJOR version).
SCHEMA_VERSION_PREFIX = "v0"

# The JSON Schema base URI.
SCHEMA_BASE_URI = f"https://weaver-spec.dev/contracts/{SCHEMA_VERSION_PREFIX}"


def is_compatible(other_version: str) -> bool:
    """Return True if other_version is compatible with the current contract version.

    Two versions are compatible if they share the same MAJOR version number.
    This reflects the spec promise: no breaking changes within a major version.

    Args:
        other_version: A semver string like "0.1.0" or "0.2.3".

    Returns:
        True if the MAJOR version matches.

    Raises:
        ValueError: If other_version is not a valid semver string.
    """
    try:
        other_major = int(other_version.split(".")[0])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"Invalid version string: {other_version!r}") from exc

    current_major = int(CONTRACT_VERSION.split(".")[0])
    return other_major == current_major
