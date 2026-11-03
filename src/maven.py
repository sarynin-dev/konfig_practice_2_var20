"""Maven POM fetching and dependency extraction module."""

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from xml.etree.ElementTree import Element, fromstring

HTTP_TIMEOUT_SECONDS = 15
HTTP_OK_STATUS = 200
COORDINATE_PARTS_WITH_VERSION = 3
COORDINATE_PARTS_WITHOUT_VERSION = 2
GROUP_INDEX = 0
ARTIFACT_INDEX = 1
VERSION_INDEX = 2
DOT_CHAR = "."
SLASH_CHAR = "/"
SCOPE_TEST = "test"
SCOPE_PROVIDED = "provided"
TAG_DEPENDENCIES = "dependencies"
TAG_DEPENDENCY = "dependency"
TAG_GROUP_ID = "groupId"
TAG_ARTIFACT_ID = "artifactId"
TAG_VERSION = "version"
TAG_SCOPE = "scope"
TAG_OPTIONAL = "optional"
TAG_PROPERTIES = "properties"
TAG_PARENT = "parent"
PROP_PATTERN = re.compile(r"\$\{([^}]+)\}")


@dataclass(frozen=True)
class MavenCoordinate:
    """Maven package coordinate representation."""

    group_id: str
    artifact_id: str
    version: str | None = None

    def to_string(self) -> str:
        """Return canonical string representation."""
        if self.version:
            return f"{self.group_id}:{self.artifact_id}:{self.version}"
        return f"{self.group_id}:{self.artifact_id}"

    def package_id(self) -> str:
        """Return unique package identifier."""
        return f"{self.group_id}:{self.artifact_id}"


class MavenError(RuntimeError):
    """Exception raised for Maven repository or POM errors."""


def parse_coordinate(coord_str: str) -> MavenCoordinate:
    """Parse string coordinate into MavenCoordinate object."""
    parts = [part.strip() for part in coord_str.split(":")]
    parts_count = len(parts)
    if parts_count == COORDINATE_PARTS_WITH_VERSION:
        return MavenCoordinate(
            group_id=parts[GROUP_INDEX],
            artifact_id=parts[ARTIFACT_INDEX],
            version=parts[VERSION_INDEX],
        )
    if parts_count == COORDINATE_PARTS_WITHOUT_VERSION:
        return MavenCoordinate(
            group_id=parts[GROUP_INDEX],
            artifact_id=parts[ARTIFACT_INDEX],
            version=None,
        )
    raise MavenError(f"Invalid Maven coordinate format: {coord_str}")


def _clean_tag(tag: str) -> str:
    """Remove XML namespace from tag name."""
    return tag.split("}")[-1]


def _build_pom_url(
    repo_url: str,
    group_id: str,
    artifact_id: str,
    version: str,
) -> str:
    """Build repository URL to artifact POM file."""
    base = repo_url.rstrip(SLASH_CHAR)
    group_path = group_id.replace(DOT_CHAR, SLASH_CHAR)
    return (
        f"{base}/{group_path}/{artifact_id}/{version}/"
        f"{artifact_id}-{version}.pom"
    )


def _fetch_url_content(url: str) -> str:
    """Fetch text content from HTTP or HTTPS URL."""
    headers = {"User-Agent": "Maven-Dependency-Visualizer/1.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as res:
            charset = res.headers.get_content_charset() or "utf-8"
            return res.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as err:
        raise MavenError(f"HTTP {err.code} while fetching {url}") from err
    except urllib.error.URLError as err:
        raise MavenError(f"Failed to connect to {url}: {err.reason}") from err


def resolve_latest_version(repo_url: str, coord: MavenCoordinate) -> str:
    """Resolve latest released version from repository metadata."""
    base = repo_url.rstrip(SLASH_CHAR)
    group_path = coord.group_id.replace(DOT_CHAR, SLASH_CHAR)
    meta_url = (
        f"{base}/{group_path}/{coord.artifact_id}/maven-metadata.xml"
    )
    content = _fetch_url_content(meta_url)
    root = fromstring(content)
    release = root.findtext(".//release")
    latest = root.findtext(".//latest")
    version = release or latest
    if not version:
        raise MavenError(
            f"Could not resolve version for {coord.to_string()} from metadata"
        )
    return version.strip()


def fetch_pom(repo_url: str, coord: MavenCoordinate) -> tuple[str, str]:
    """Fetch POM XML content and return resolved version with XML string."""
    version = coord.version
    if not version:
        version = resolve_latest_version(repo_url, coord)
    pom_url = _build_pom_url(
        repo_url,
        coord.group_id,
        coord.artifact_id,
        version,
    )
    content = _fetch_url_content(pom_url)
    return version, content


def _extract_properties(root: Element) -> dict[str, str]:
    """Extract Maven POM property mapping."""
    props: dict[str, str] = {}
    for elem in root:
        if _clean_tag(elem.tag) == TAG_PROPERTIES:
            for child in elem:
                key = _clean_tag(child.tag)
                props[key] = (child.text or "").strip()
    return props


def _substitute_properties(val: str, props: dict[str, str]) -> str:
    """Substitute Maven property placeholders in string."""
    def _replace(match: re.Match[str]) -> str:
        """Replace regex match with property value if found."""
        key = match.group(1)
        return props.get(key, match.group(0))

    return PROP_PATTERN.sub(_replace, val)


def _is_direct_dependency(dep_elem: Element) -> bool:
    """Check if dependency should be included in direct dependencies."""
    scope_val = dep_elem.findtext(TAG_SCOPE)
    if not scope_val:
        for child in dep_elem:
            if _clean_tag(child.tag) == TAG_SCOPE:
                scope_val = child.text
                break
    scope_str = (scope_val or "").strip().lower()
    if scope_str in (SCOPE_TEST, SCOPE_PROVIDED):
        return False
    return True


def _parse_single_dep(
    elem: Element,
    props: dict[str, str],
) -> MavenCoordinate | None:
    """Parse a single dependency element into MavenCoordinate."""
    fields: dict[str, str] = {}
    for child in elem:
        tag_name = _clean_tag(child.tag)
        fields[tag_name] = (child.text or "").strip()

    group_id = fields.get(TAG_GROUP_ID)
    artifact_id = fields.get(TAG_ARTIFACT_ID)
    if not group_id or not artifact_id:
        return None

    raw_version = fields.get(TAG_VERSION)
    version = None
    if raw_version:
        version = _substitute_properties(raw_version, props)
        if version.startswith("${") and version.endswith("}"):
            version = None

    return MavenCoordinate(
        group_id=_substitute_properties(group_id, props),
        artifact_id=_substitute_properties(artifact_id, props),
        version=version,
    )


def extract_direct_dependencies(pom_xml: str) -> list[MavenCoordinate]:
    """Extract direct dependencies from POM XML content."""
    root = fromstring(pom_xml)
    props = _extract_properties(root)
    results: list[MavenCoordinate] = []

    deps_elem = None
    for child in root:
        if _clean_tag(child.tag) == TAG_DEPENDENCIES:
            deps_elem = child
            break

    if deps_elem is None:
        return results

    for child in deps_elem:
        if _clean_tag(child.tag) == TAG_DEPENDENCY:
            if not _is_direct_dependency(child):
                continue
            coord = _parse_single_dep(child, props)
            if coord is not None:
                results.append(coord)
    return results


def get_direct_dependencies(
    repo_url: str,
    coord_str: str,
) -> tuple[str, list[MavenCoordinate]]:
    """Fetch POM and return resolved coordinate string and dependencies."""
    coord = parse_coordinate(coord_str)
    resolved_version, pom_xml = fetch_pom(repo_url, coord)
    resolved_coord = MavenCoordinate(
        group_id=coord.group_id,
        artifact_id=coord.artifact_id,
        version=resolved_version,
    )
    deps = extract_direct_dependencies(pom_xml)
    return resolved_coord.to_string(), deps
