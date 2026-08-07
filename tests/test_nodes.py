"""
Unit tests for NodeSchema.
"""

import pytest
from pydantic import ValidationError
from struct_core.structural_model.nodes import Node


def test_node_creation_2d():
    node = Node(id=1, x=10.0, y=5.0)
    assert node.id == 1
    assert node.x == 10.0
    assert node.y == 5.0
    assert node.z == 0.0
    assert node.mass == 0.0
    assert node.inertia == 0.0


def test_node_creation_3d_with_mass():
    node = Node(id="N2", x=0.0, y=0.0, z=12.0, mass=500.0, inertia=250.0)
    assert node.id == "N2"
    assert node.z == 12.0
    assert node.mass == 500.0
    assert node.inertia == 250.0


def test_node_invalid_mass():
    with pytest.raises(ValidationError):
        Node(id=1, x=0.0, y=0.0, mass=-10.0)
