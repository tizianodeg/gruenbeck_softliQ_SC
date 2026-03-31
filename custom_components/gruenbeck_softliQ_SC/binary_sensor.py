"""Binary sensor platform for Gruenbeck SoftliQ SC integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SoftQLinkDataUpdateCoordinator
from .entity import build_device_info, get_entity_unique_id_prefix


@dataclass(frozen=True)
class SoftQLinkBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing SoftQLink binary sensor entities."""


BINARY_SENSOR_DESCRIPTIONS: tuple[SoftQLinkBinarySensorEntityDescription, ...] = (
    SoftQLinkBinarySensorEntityDescription(
        key="regeneration_running",
        translation_key="regeneration_running",
        icon="mdi:water-sync",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gruenbeck binary sensor entities."""
    coordinator: SoftQLinkDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities(
        SoftQLinkBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class SoftQLinkBinarySensor(
    CoordinatorEntity[SoftQLinkDataUpdateCoordinator], BinarySensorEntity
):
    """Representation of a SoftQLink binary sensor."""

    entity_description: SoftQLinkBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SoftQLinkDataUpdateCoordinator,
        description: SoftQLinkBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        unique_id_prefix = get_entity_unique_id_prefix(coordinator)
        self._attr_unique_id = f"{unique_id_prefix}-{description.key}".lower()
        self._attr_device_info = build_device_info(coordinator)
        self._update_attrs()

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return super().available and "D_B_1" in self.coordinator.data

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_attrs()
        self.async_write_ha_state()

    def _update_attrs(self) -> None:
        """Update the entity state from coordinator data."""
        self._attr_is_on = self.coordinator.data.get("D_B_1") == "1"
