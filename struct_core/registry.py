"""
Lightweight registry mechanism for custom element types.
"""

from typing import Dict, Type


class ElementRegistry:
    """
    Registry for dynamic element type registration.
    """
    _registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, type_name: str):
        """
        Decorator to register a custom element schema class.
        """
        def decorator(subclass: Type):
            cls._registry[type_name] = subclass
            return subclass
        return decorator

    @classmethod
    def get(cls, type_name: str) -> Type:
        """
        Get registered element schema class by type name.
        """
        if type_name not in cls._registry:
            raise KeyError(f"Element type '{type_name}' is not registered.")
        return cls._registry[type_name]

    @classmethod
    def list_types(cls) -> list[str]:
        """
        List all registered element type names.
        """
        return list(cls._registry.keys())
