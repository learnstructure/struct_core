"""
Project schema representing the top-level container combining metadata and structural models.
"""

from pydantic import Field
from .base import BaseSchemaModel
from .metadata import Metadata
from .model import StructuralModel


class Project(BaseSchemaModel):
    """
    Top-level project aggregate wrapping metadata header and structural model data.
    """
    metadata: Metadata = Field(default_factory=Metadata, description="Project metadata and engineering units")
    model: StructuralModel = Field(default_factory=StructuralModel, description="Structural model data container")
