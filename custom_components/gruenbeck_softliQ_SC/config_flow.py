"""Config flow for Gruenbeck Water softener local integration."""
from __future__ import annotations

import logging
import socket
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .softQLinkMuxClient import SoftQLinkMuxClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str, hass: HomeAssistant) -> None:
        """Initialize."""
        self.host = host
        self.hass = hass

    async def authenticate(self) -> bool:
        """Try to open a connection to the given host."""
        try:
            websession: aiohttp.ClientSession = async_get_clientsession(self.hass)
            muxClient = await SoftQLinkMuxClient.create(self.host,websession)
            return muxClient.connected
        except Exception as exc:
            raise CannotConnect from exc

    def resolveName(self):
        """Try to find a fqn name for this address."""
        try:
            fqdn = socket.gethostbyaddr(self.host)[0]
            return fqdn
        except socket.herror:
            return self.host


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    hub = PlaceholderHub(data[CONF_HOST], hass=hass)

    if not await hub.authenticate():
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": hub.resolveName()}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gruenbeck Water softener local."""

    VERSION = 1
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
