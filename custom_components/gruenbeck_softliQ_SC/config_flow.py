"""Config flow for Gruenbeck Water softener local integration."""
from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession 

from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN
from .softQLinkMuxClient import SoftQLinkMuxClient

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
    muxClient = await SoftQLinkMuxClient.create(data[CONF_HOST], websession)
    if not muxClient.connected:
        raise CannotConnect
    return True


class GruenBeckConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gruenbeck softliQ SC."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult :
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", str(e))
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
        old_entries = self.hass.config_entries.async_entries(OLD_DOMAIN)
        if(old_entries):
            for old_entry in old_entries:

                _LOGGER.warning("Migrating config entry from %s to %s", OLD_DOMAIN, DOMAIN)

                # Save original entry data
                data = dict(old_entry.data)
                options = dict(old_entry.options)
                title = old_entry.title
                version = old_entry.version
                entry_id = old_entry.entry_id
                source = old_entry.source
                unique_id = old_entry.unique_id

               
                # Re-add the entry manually under the new domain
                migrated_entry = ConfigEntry(
                    version=version,
                    domain=DOMAIN,
                    title=title,
                    data=data,
                    options=options,
                    source=source,
                    entry_id=entry_id,
                    unique_id=unique_id,
                    discovery_keys= old_entry.discovery_keys,
                    subentries_data=None,
                    minor_version= old_entry.minor_version
                )
                
                # Remove the old entry from the registry
                old_entry.discovery_keys = MappingProxyType({})
                await self.hass.config_entries.async_remove(entry_id)
                _LOGGER.info("Removed old config entry: %s", entry_id)

                await self.hass.config_entries.async_add(migrated_entry) 

                # Update device identifiers
                dev_reg = dr.async_get(self.hass)
                for device in list(dev_reg.devices.values()):
                    if any(iden[0] == OLD_DOMAIN for iden in device.identifiers):
                        new_ids = {
                            (DOMAIN if iden[0] == OLD_DOMAIN else iden[0], iden[1])
                            for iden in device.identifiers
                        }
                        dev_reg.async_update_device(device.id, new_identifiers=new_ids)
                        _LOGGER.info("Updated device identifiers for device %s", device.id)

                _LOGGER.info("Re-registered config entry %s under new domain %s", entry_id, DOMAIN)

                # Set up the migrated entry
                await self.hass.config_entries.async_setup(entry_id)
            return self.async_abort(reason= "migrated", description_placeholders=None)
        else:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
