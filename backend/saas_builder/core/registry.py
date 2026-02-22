"""ExtensionRegistry — discovers and holds all registered extensions."""

from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

from .base import ExtensionBase

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ExtensionRegistry:
    """Singleton registry of all available extensions."""

    _instance: "ExtensionRegistry | None" = None

    def __new__(cls) -> "ExtensionRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._extensions: dict[str, ExtensionBase] = {}
        return cls._instance

    def register(self, ext: ExtensionBase) -> None:
        if ext.name in self._extensions:
            logger.warning("Extension '%s' already registered — overwriting", ext.name)
        self._extensions[ext.name] = ext
        logger.info("Registered extension: %s v%s", ext.name, ext.version)

    def get(self, name: str) -> ExtensionBase | None:
        return self._extensions.get(name)

    def all(self) -> dict[str, ExtensionBase]:
        return dict(self._extensions)

    def names(self) -> list[str]:
        return list(self._extensions.keys())

    def discover(self, extensions_path: str | Path) -> None:
        """Auto-discover and register all extensions in a directory.

        Each subdirectory should have an `extension.py` with a class
        that subclasses ExtensionBase.
        """
        extensions_path = Path(extensions_path)
        if not extensions_path.exists():
            logger.warning("Extensions path does not exist: %s", extensions_path)
            return

        for item in sorted(extensions_path.iterdir()):
            if not item.is_dir() or item.name.startswith("_"):
                continue
            ext_file = item / "extension.py"
            if not ext_file.exists():
                continue
            try:
                module_name = f"extensions.{item.name}.extension"
                module = importlib.import_module(module_name)
                # Find the ExtensionBase subclass
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, ExtensionBase)
                        and attr is not ExtensionBase
                        and attr.name
                    ):
                        instance = attr()
                        self.register(instance)
                        break
            except Exception:
                logger.exception("Failed to load extension from %s", item)

    def clear(self) -> None:
        self._extensions.clear()
        ExtensionRegistry._instance = None
