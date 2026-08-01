"""
Serialization helpers for JSON and Python dictionary conversion.
"""

from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def to_dict(obj: BaseModel) -> dict:
    """
    Convert a schema object to a Python dictionary.
    """
    return obj.model_dump()


def from_dict(model_class: Type[T], data: dict) -> T:
    """
    Instantiate a schema object from a Python dictionary.
    """
    return model_class.model_validate(data)


def to_json(obj: BaseModel, indent: int = 2) -> str:
    """
    Serialize a schema object to a JSON formatted string.
    """
    return obj.model_dump_json(indent=indent)


def from_json(model_class: Type[T], json_str: str) -> T:
    """
    Deserialize a schema object from a JSON string.
    """
    return model_class.model_validate_json(json_str)


def save_json(obj: BaseModel, file_path: str, indent: int = 2) -> None:
    """
    Save a schema object to a JSON file.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(to_json(obj, indent=indent))


def load_json(model_class: Type[T], file_path: str) -> T:
    """
    Load a schema object from a JSON file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return from_json(model_class, f.read())
