"""Config flow for Gruenbeck Water softener local integration."""

from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CURRENT_VERSION
from .softQLinkMuxClient import SoftQLinkClientError, SoftQLinkMuxClient

_LOGGER = logging.getLogger(__name__)
OLD_DOMAIN = "gruenbeck_softliQ_SC"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_HOST): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> bool:
    """Validate the user input allows us to connect.
    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    websession: aiohttp.ClientSession = async_get_clientsession(hass)
    mux_client = await SoftQLinkMuxClient.create(data[CONF_HOST], websession)
    if not mux_client.connected:
        raise CannotConnect
    return True


class GruenBeckConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gruenbeck softliQ SC."""

    VERSION = CURRENT_VERSION

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            if old_entries := self.hass.config_entries.async_entries(OLD_DOMAIN):
                return await self._async_migrate_old_entry(old_entries[0])

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self.async_set_unique_id(user_input[CONF_HOST].lower())
                self._abort_if_unique_id_configured()
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except SoftQLinkClientError as err:
                _LOGGER.debug(
                    "Validation failed for host %s: %s",
                    user_input[CONF_HOST],
                    err,
                )
                errors["base"] = "cannot_connect"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", str(e))
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _async_migrate_old_entry(
        self, old_entry: ConfigEntry[Any]
    ) -> ConfigFlowResult:
        """Re-register a legacy config entry under the new domain."""
        host = old_entry.data.get(CONF_HOST)
        if not host:
            _LOGGER.warning(
                "Skipping migration of legacy entry %s because host is missing",
                old_entry.entry_id,
            )
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        migrated_entry = ConfigEntry(
            version=old_entry.version,
            domain=DOMAIN,
            title=old_entry.title,
            data=dict(old_entry.data),
            options=dict(old_entry.options),
            source=old_entry.source,
            entry_id=old_entry.entry_id,
            unique_id=old_entry.unique_id or host.lower(),
            discovery_keys=old_entry.discovery_keys,
            subentries_data=None,
            minor_version=old_entry.minor_version,
        )

        old_entry.discovery_keys = MappingProxyType({})
        await self.hass.config_entries.async_remove(old_entry.entry_id)
        await self.hass.config_entries.async_add(migrated_entry)

        return ConfigFlowResult(
            step_id="user",
            type=FlowResultType.SHOW_PROGRESS_DONE,
            flow_id=self.flow_id,
            handler="",
            reason="migration was done",
            translation_domain=DOMAIN,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
