"""
Element type registry for struct_core.structural_model.

Provides a central registry for mapping element type strings to their
concrete schema classes. Solvers and design packages can register
custom element types at runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Type

if TYPE_CHECKING:
    from .elements import BaseElement


class _ElementRegistry:
    """
    A simple registry mapping element type strings to their Python classes.

    Usage::

        from struct_core.structural_model.registry import ElementRegistry

        # Register a custom element type
        @ElementRegistry.register("custom_beam")
        class CustomBeamElement(BeamElement):
            pass

        # Look up a registered type
        cls = ElementRegistry.get("custom_beam")
    """

    def __init__(self) -> None:
        self._registry: dict[str, Type] = {}

    def register(self, type_name: str) -> Callable[[Type], Type]:
        """Class decorator that registers an element class under *type_name*."""

        def decorator(cls: Type) -> Type:
            self._registry[type_name] = cls
            return cls

        return decorator

    def get(self, type_name: str) -> Type:
        """Return the class registered under *type_name*.

        Raises
        ------
        KeyError
            If *type_name* has not been registered.
        """
        if type_name not in self._registry:
            raise KeyError(
                f"Unknown element type '{type_name}'. "
                f"Registered types: {list(self._registry)}"
            )
        return self._registry[type_name]

    def list_types(self) -> list[str]:
        """Return all currently registered type names."""
        return list(self._registry.keys())

    def __contains__(self, type_name: str) -> bool:
        return type_name in self._registry

    def __repr__(self) -> str:  # pragma: no cover
        return f"ElementRegistry({list(self._registry)})"


# Singleton instance used across the ecosystem
ElementRegistry = _ElementRegistry()
