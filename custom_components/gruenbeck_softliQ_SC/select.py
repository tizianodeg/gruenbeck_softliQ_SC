"""Select platform for Gruenbeck SoftliQ SC integration."""

from __future__ import annotations

from typing import Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SoftQLinkDataUpdateCoordinator
from .entity import build_device_info, get_entity_unique_id_prefix


class SoftQLinkSelectEntityDescription(SelectEntityDescription):
    """Base class for a Softliq select entity description."""


SELECT_DESCRIPTIONS: Final = [
    SoftQLinkSelectEntityDescription(
        key="D_C_5_1",
        translation_key="D_C_5_1",
        entity_category=None,
        options=["0", "1", "2", "3"],
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    selects = []
    for description in SELECT_DESCRIPTIONS:
        selects.append(SoftQLinkSelectEntity(coordinator, description))
    async_add_entities(selects)


class SoftQLinkSelectEntity(
    CoordinatorEntity[SoftQLinkDataUpdateCoordinator], SelectEntity
):
    """Representation of a SoftQLink select entity."""

    entity_description: SoftQLinkSelectEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SoftQLinkDataUpdateCoordinator,
        description: SoftQLinkSelectEntityDescription,
    ) -> None:
        """Initialize a select."""
        super().__init__(coordinator)
        self.entity_description = description
        unique_id_prefix = get_entity_unique_id_prefix(coordinator)
        self._attr_unique_id = f"{unique_id_prefix}-{description.key}".lower()
        self._attr_device_info = build_device_info(coordinator)
        self._handle_value_update()

    async def async_select_option(self, option: str) -> None:
        """Update the current selected option."""
        await self.coordinator.client.set_mode(option)
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._handle_value_update()
        self.async_write_ha_state()

    def _handle_value_update(self) -> None:
        """Update the current selected option from coordinator data."""
        current_option = self.coordinator.data.get(self.entity_description.key)
        self._attr_current_option = (
            current_option
            if current_option in self.entity_description.options
            else None
        )
