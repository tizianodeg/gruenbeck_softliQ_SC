"""Button platform for Gruenbeck SoftliQ SC integration."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SoftQLinkDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SoftQLinkButtonEntityDescription(ButtonEntityDescription):
    """Class describing SoftQLink button entities."""


BUTTON_DESCRIPTIONS: tuple[SoftQLinkButtonEntityDescription, ...] = (
    SoftQLinkButtonEntityDescription(
        key="manual_regeneration",
        translation_key="manual_regeneration",
        icon="mdi:refresh",
    ),
    SoftQLinkButtonEntityDescription(
        key="reset_error_memory",
        translation_key="reset_error_memory",
        icon="mdi:alert-remove",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gruenbeck button entities."""
    coordinator: SoftQLinkDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        SoftQLinkButtonEntity(coordinator, description)
        for description in BUTTON_DESCRIPTIONS
    )


class SoftQLinkButtonEntity(CoordinatorEntity[SoftQLinkDataUpdateCoordinator], ButtonEntity):
    """Representation of a SoftQLink button."""

    entity_description: SoftQLinkButtonEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SoftQLinkDataUpdateCoordinator,
        description: SoftQLinkButtonEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.name}-{description.key}".lower()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.name}")},
            name=coordinator.name,
            manufacturer="Gruenbeck",
            model=coordinator.clientMuxClient.model,
            sw_version=coordinator.clientMuxClient.sw_version,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            if self.entity_description.key == "manual_regeneration":
                await self.coordinator.clientMuxClient.startManualRegeneration()
            elif self.entity_description.key == "reset_error_memory":
                await self.coordinator.clientMuxClient.resetErrorMemory()
        except Exception as e:
            _LOGGER.error("Gruenbeck button press failed: %s", e)
            raise
