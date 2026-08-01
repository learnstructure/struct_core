"""
Unit tests for BaseSchemaModel and base types.
"""

import pytest
from pydantic import ValidationError
from struct_core.base import BaseSchemaModel


class SampleModel(BaseSchemaModel):
    name: str
    value: float


def test_base_schema_valid():
    model = SampleModel(name="test", value=12.5)
    assert model.name == "test"
    assert model.value == 12.5


def test_base_schema_forbid_extra():
    with pytest.raises(ValidationError):
        SampleModel(name="test", value=12.5, extra_field="not_allowed")  # type: ignore


test_base_schema_assignment_validation_data = {"name": "test", "value": 10.0}


def test_base_schema_assignment_validation():
    model = SampleModel(**test_base_schema_assignment_validation_data)
    model.name = "updated"
    assert model.name == "updated"
    with pytest.raises(ValidationError):
        model.value = "invalid_float"  # type: ignore
