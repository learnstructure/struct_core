"""
Unit tests for metadata and units schemas.
"""

from struct_core.metadata import Metadata, Units


def test_units_defaults():
    units = Units()
    assert units.length == "m"
    assert units.force == "kN"
    assert units.time == "s"
    assert units.mass == "kg"
    assert units.temperature == "C"


def test_units_custom():
    units = Units(length="in", force="kip", mass="slug")
    assert units.length == "in"
    assert units.force == "kip"
    assert units.mass == "slug"


def test_metadata_defaults():
    meta = Metadata(title="Test Frame", author="Engineer")
    assert meta.schema_version == "1.0.0"
    assert meta.title == "Test Frame"
    assert meta.author == "Engineer"
    assert meta.units.length == "m"
    assert meta.created_at is not None


def test_metadata_serialization():
    meta = Metadata(title="Portal Frame", project_name="Building A")
    data = meta.model_dump()
    assert data["title"] == "Portal Frame"
    assert data["project_name"] == "Building A"
    assert data["units"]["length"] == "m"

    reconstructed = Metadata.model_validate(data)
    assert reconstructed.title == meta.title
    assert reconstructed.units.length == "m"
