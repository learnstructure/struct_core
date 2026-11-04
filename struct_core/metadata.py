"""
Metadata and Units schemas for structural models.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from .units import Units


class Metadata(BaseModel):
    """
    Metadata header for a structural model or project.
    """
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: str = Field(default="2.0.0", description="Semantic version of the schema format (2.0: sections own their material)")
    title: Optional[str] = Field(default=None, description="Title of the model or analysis")
    project_name: Optional[str] = Field(default=None, description="Name of the structural project")
    author: Optional[str] = Field(default=None, description="Author or engineer name")
    description: Optional[str] = Field(default=None, description="Detailed description of the model")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 creation timestamp"
    )
    units: Units = Field(default_factory=Units, description="Engineering units system")

    _project: Any = PrivateAttr(default=None)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name == "units" and getattr(self, "_project", None) is not None:
            proj = self._project
            if getattr(proj, "model", None) is not None:
                proj.model.units = self.units
