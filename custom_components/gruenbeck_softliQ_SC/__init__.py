"""The Gruenbeck Water softener local integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import SoftQLinkDataUpdateCoordinator
from .softQLinkMuxClient import SoftQLinkMuxClient

# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gruenbeck Water softener local from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    websession = async_get_clientsession(hass)
    muxClient = await SoftQLinkMuxClient.create(entry.data["host"],websession)
    coordinator = SoftQLinkDataUpdateCoordinator(
        hass, entry.title, muxClient
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
