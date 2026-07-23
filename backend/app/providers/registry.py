"""
Provider Registry

Central registry for registering, discovering, and accessing active `JobDiscoveryProvider` plugins.

Adding a new discovery source to Finder requires ONLY:
1. Creating a class implementing `JobDiscoveryProvider` (or subclass `ATSProvider`, `SearchEngineProvider`, `CrawlerProvider`).
2. Registering an instance here via `registry.register_provider(...)`.
Zero changes to `JobSearchService` are required.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.providers.base_discovery import JobDiscoveryProvider, ProviderType
from app.providers.greenhouse import GreenhouseProvider
from app.providers.lever import LeverProvider
from app.providers.ashby import AshbyProvider
from app.schemas.job import ProviderInfo

logger = logging.getLogger(__name__)


@dataclass
class RegisteredProviderMeta:
    """
    Metadata for registered discovery provider entries.
    """
    provider: JobDiscoveryProvider
    enabled: bool = True
    priority: int = 100
    capabilities: List[str] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class ProviderRegistry:
    """
    Registry for managing available and active JobDiscoveryProvider implementations.
    """

    def __init__(self):
        self._entries: Dict[str, RegisteredProviderMeta] = {}

    def register_provider(
        self,
        provider: JobDiscoveryProvider,
        enabled: bool = True,
        priority: int = 100,
        capabilities: Optional[List[str]] = None
    ) -> None:
        """
        Register a new discovery provider instance in the application registry.
        """
        key = provider.source_name
        meta = RegisteredProviderMeta(
            provider=provider,
            enabled=enabled,
            priority=priority,
            capabilities=capabilities or []
        )
        self._entries[key] = meta
        logger.info(f"Registered job discovery provider: '{key}' ({provider.display_name}) [Type: {provider.provider_type.value}]")

    def set_provider_enabled(self, source_name: str, enabled: bool) -> bool:
        """
        Dynamically enable or disable a provider without modifying code.
        """
        if source_name in self._entries:
            self._entries[source_name].enabled = enabled
            return True
        return False

    def get_provider(self, source_name: str) -> Optional[JobDiscoveryProvider]:
        """
        Retrieve a specific discovery provider by its source identifier.
        """
        entry = self._entries.get(source_name)
        return entry.provider if entry else None

    def get_enabled_providers(self, provider_type: Optional[ProviderType] = None) -> List[JobDiscoveryProvider]:
        """
        Retrieve all currently enabled providers, sorted by priority (lowest integer = highest priority).
        Optionally filter by `ProviderType` (ATS, SEARCH_ENGINE, CRAWLER).
        """
        sorted_entries = sorted(
            self._entries.values(),
            key=lambda entry: entry.priority
        )

        providers: List[JobDiscoveryProvider] = []
        for entry in sorted_entries:
            if not entry.enabled:
                continue
            if provider_type and entry.provider.provider_type != provider_type:
                continue
            providers.append(entry.provider)

        return providers

    def list_providers_info(self) -> List[ProviderInfo]:
        """
        Return metadata for all registered providers.
        """
        info_list: List[ProviderInfo] = []
        for name, entry in self._entries.items():
            p = entry.provider
            info_list.append(
                ProviderInfo(
                    name=p.source_name,
                    display_name=p.display_name,
                    description=p.description,
                    enabled=entry.enabled
                )
            )
        return info_list


# Singleton registry instance initialized with default ATS discovery providers
registry = ProviderRegistry()
registry.register_provider(GreenhouseProvider(), priority=10)
registry.register_provider(LeverProvider(), priority=20)
registry.register_provider(AshbyProvider(), priority=30)
