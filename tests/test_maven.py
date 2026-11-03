"""Unit tests for Maven POM parsing and coordinate handling."""

import unittest
from src.maven import (
    MavenCoordinate,
    MavenError,
    extract_direct_dependencies,
    parse_coordinate,
)

SAMPLE_POM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>org.example</groupId>
    <artifactId>sample-lib</artifactId>
    <version>1.0.0</version>
    <properties>
        <dep.version>2.5.0</dep.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
            <version>${dep.version}</version>
            <scope>compile</scope>
        </dependency>
        <dependency>
            <groupId>com.google.guava</groupId>
            <artifactId>guava</artifactId>
            <version>31.0</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""


class TestMaven(unittest.TestCase):
    """Test suite for Maven coordinate parsing and POM extraction."""

    def test_parse_coordinate_with_version(self) -> None:
        """Test parsing full coordinate with explicit version."""
        coord = parse_coordinate("org.example:my-lib:2.1.0")
        self.assertEqual(coord.group_id, "org.example")
        self.assertEqual(coord.artifact_id, "my-lib")
        self.assertEqual(coord.version, "2.1.0")
        self.assertEqual(coord.to_string(), "org.example:my-lib:2.1.0")

    def test_parse_coordinate_without_version(self) -> None:
        """Test parsing coordinate without version."""
        coord = parse_coordinate("org.example:my-lib")
        self.assertEqual(coord.group_id, "org.example")
        self.assertEqual(coord.artifact_id, "my-lib")
        self.assertIsNone(coord.version)
        self.assertEqual(coord.to_string(), "org.example:my-lib")

    def test_parse_coordinate_invalid(self) -> None:
        """Test error when coordinate format has invalid parts."""
        with self.assertRaises(MavenError):
            parse_coordinate("single_token")

    def test_extract_direct_dependencies(self) -> None:
        """Test extracting direct compile dependencies with properties."""
        deps = extract_direct_dependencies(SAMPLE_POM_XML)
        dep_names = [d.to_string() for d in deps]
        self.assertIn("org.slf4j:slf4j-api:2.5.0", dep_names)
        self.assertIn("com.google.guava:guava:31.0", dep_names)
        self.assertNotIn("junit:junit:4.13.2", dep_names)

    def test_empty_dependencies_pom(self) -> None:
        """Test POM XML with no dependencies section."""
        xml = (
            "<project><groupId>a</groupId>"
            "<artifactId>b</artifactId></project>"
        )
        deps = extract_direct_dependencies(xml)
        self.assertFalse(deps)


if __name__ == "__main__":
    unittest.main()
