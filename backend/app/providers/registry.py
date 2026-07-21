"""
Provider Registry

Central registry for registering, discovering, and accessing active `JobProvider` plugins.

Adding a new provider to Finder requires:
1. Creating a class implementing `JobProvider`.
2. Registering an instance here via `registry.register_provider(...)`.
"""

import logging
from typing import Dict, List, Optional

from app.providers.base import JobProvider
from app.providers.greenhouse import GreenhouseProvider
from app.providers.lever import LeverProvider
from app.providers.ashby import AshbyProvider
from app.schemas.job import ProviderInfo

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry for managing available and active JobProvider implementations.
    """

    def __init__(self):
        self._providers: Dict[str, JobProvider] = {}
        self._enabled: Dict[str, bool] = {}

    def register_provider(self, provider: JobProvider, enabled: bool = True) -> None:
        """
        Register a new provider instance in the application registry.
        """
        key = provider.source_name
        self._providers[key] = provider
        self._enabled[key] = enabled
        logger.info(f"Registered job provider: '{key}' ({provider.display_name})")

    def get_provider(self, source_name: str) -> Optional[JobProvider]:
        """
        Retrieve a specific provider by its source identifier.
        """
        return self._providers.get(source_name)

    def get_enabled_providers(self) -> List[JobProvider]:
        """
        Retrieve all currently enabled providers.
        """
        return [
            provider for name, provider in self._providers.items()
            if self._enabled.get(name, True)
        ]

    def list_providers_info(self) -> List[ProviderInfo]:
        """
        Return metadata for all registered providers.
        """
        info_list: List[ProviderInfo] = []
        for name, provider in self._providers.items():
            info_list.append(
                ProviderInfo(
                    name=provider.source_name,
                    display_name=provider.display_name,
                    description=provider.description,
                    enabled=self._enabled.get(name, True)
                )
            )
        return info_list


# Singleton registry instance initialized with default providers
registry = ProviderRegistry()
registry.register_provider(GreenhouseProvider())
registry.register_provider(LeverProvider())
registry.register_provider(AshbyProvider())
