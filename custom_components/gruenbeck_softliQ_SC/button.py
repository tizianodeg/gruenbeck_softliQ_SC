"""Button platform for Gruenbeck SoftliQ SC integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SoftQLinkDataUpdateCoordinator
from .entity import build_device_info, get_entity_unique_id_prefix

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
    coordinator: SoftQLinkDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities(
        SoftQLinkButtonEntity(coordinator, description)
        for description in BUTTON_DESCRIPTIONS
    )


class SoftQLinkButtonEntity(
    CoordinatorEntity[SoftQLinkDataUpdateCoordinator], ButtonEntity
):
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
        unique_id_prefix = get_entity_unique_id_prefix(coordinator)
        self._attr_unique_id = f"{unique_id_prefix}-{description.key}".lower()
        self._attr_device_info = build_device_info(coordinator)

    @property
    def available(self) -> bool:
        """Return if the button is available."""
        if not super().available:
            return False
        if self.coordinator.button_action_in_progress:
            return False
        if self.entity_description.key != "manual_regeneration":
            return True
        return self.coordinator.data.get("D_B_1") == "0"

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            if self.coordinator.button_action_in_progress:
                raise HomeAssistantError("Another button action is already running")
            if self.entity_description.key == "manual_regeneration":
                if self.coordinator.data.get("D_B_1") != "0":
                    raise HomeAssistantError("Manual regeneration is already running")
                self.coordinator.set_active_button_action(self.entity_description.key)
                await self.coordinator.client.start_manual_regeneration()
                await self.coordinator.async_request_refresh()
            elif self.entity_description.key == "reset_error_memory":
                self.coordinator.set_active_button_action(self.entity_description.key)
                await self.coordinator.client.reset_error_memory()
                await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error("Gruenbeck button press failed: %s", e)
            raise
        finally:
            if self.coordinator.active_button_key == self.entity_description.key:
                self.coordinator.set_active_button_action(None)
