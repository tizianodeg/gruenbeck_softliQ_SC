"""DataUpdateCoordinator for the Gruenbeck integration."""

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import UPDATE_INTERVAL
from .softQLinkMuxClient import SoftQLinkClientError, SoftQLinkMuxClient

_LOGGER = logging.getLogger(__name__)


class SoftQLinkDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold softQlink data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        mux_client: SoftQLinkMuxClient,
    ) -> None:
        """Initialize."""
        self.config_entry = config_entry
        self.datacache: dict[str, Any] = {}
        self.client = mux_client
        self.button_action_in_progress = False
        self.active_button_key: str | None = None
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=config_entry.title,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    @callback
    def set_active_button_action(self, button_key: str | None) -> None:
        """Update the transient button-action state and notify entities."""
        self.button_action_in_progress = button_key is not None
        self.active_button_key = button_key
        self.async_update_listeners()

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            self.datacache = (await self.client.get_current_values()) | (
                await self.client.get_error_memory_values()
            )
        except SoftQLinkClientError as error:
            raise UpdateFailed(error) from error
        return self.datacache
