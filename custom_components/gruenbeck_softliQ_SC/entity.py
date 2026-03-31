"""Shared entity helpers for the Gruenbeck integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import SoftQLinkDataUpdateCoordinator


def get_entity_unique_id_prefix(coordinator: SoftQLinkDataUpdateCoordinator) -> str:
    """Return the legacy entity unique ID prefix."""
    return coordinator.config_entry.title.lower()


def get_device_identifier(coordinator: SoftQLinkDataUpdateCoordinator) -> str:
    """Return the legacy device identifier."""
    return coordinator.config_entry.title


def build_device_info(coordinator: SoftQLinkDataUpdateCoordinator) -> DeviceInfo:
    """Build common device info for all entities."""
    device_id = get_device_identifier(coordinator)
    return DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=coordinator.config_entry.title,
        manufacturer="Gruenbeck",
        model=coordinator.client.model,
        sw_version=coordinator.client.sw_version,
    )
