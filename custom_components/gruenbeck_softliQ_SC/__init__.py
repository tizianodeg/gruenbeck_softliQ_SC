"""The Gruenbeck Water softener local integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST

from .const import DOMAIN, CURRENT_VERSION
from .coordinator import SoftQLinkDataUpdateCoordinator
from .softQLinkMuxClient import SoftQLinkMuxClient

_LOGGER = logging.getLogger(__name__)
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [
    Platform.SENSOR, 
    Platform.SELECT,
    Platform.BUTTON,  # NEU
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gruenbeck Water softener local from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    websession = async_get_clientsession(hass)
    muxClient = await SoftQLinkMuxClient.create(entry.data[CONF_HOST], websession)
    coordinator = SoftQLinkDataUpdateCoordinator(hass, entry.title, muxClient)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
        """Migrate old entry."""
         
        if config_entry.version > CURRENT_VERSION:
            _LOGGER.fatal("entities found have a higher version than the integration version")
            # This means the user has downgraded from a future version
            return False

        if config_entry.version < CURRENT_VERSION:
            new_data = {**config_entry.data} 
            hass.config_entries.async_update_entry(config_entry, data=new_data, minor_version=0, version= CURRENT_VERSION)
      
        return True
