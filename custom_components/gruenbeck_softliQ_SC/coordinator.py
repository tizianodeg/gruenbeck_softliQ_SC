"""DataUpdateCoordinator for the Gruenbeck integration."""
from datetime import timedelta
import logging
from typing import Any

from aiohttp.client_exceptions import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import UPDATE_INTERVAL
from .softQLinkMuxClient import SoftQLinkMuxClient

_LOGGER = logging.getLogger(__name__)


class SoftQLinkDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold softQlink data."""

    def __init__(
        self, hass: HomeAssistant, name: str, muxClient: SoftQLinkMuxClient
    ) -> None:
        """Initialize."""
        self.name = name
        self.datacache: dict[str, Any] = {}
        self.clientMuxClient = muxClient
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
           self.datacache = (await self.clientMuxClient.getCurrentValues()) | (await self.clientMuxClient.getMeterValues())
        except ClientError as error:
            raise UpdateFailed(error) from error
        return self.datacache


