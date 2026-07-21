"""
Providers Package

Exposes base JobProvider interface and global ProviderRegistry singleton.
"""

from app.providers.base import JobProvider
from app.providers.registry import registry

__all__ = ["JobProvider", "registry"]
