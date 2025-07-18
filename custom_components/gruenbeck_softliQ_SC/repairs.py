# custom_components/gruenbeck_softliQ_SC/repairs.py
from __future__ import annotations

import asyncio
import voluptuous as vol

from homeassistant import data_entry_flow
from homeassistant.components.repairs import ConfirmRepairFlow
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN, NEW_DOMAIN

class DomainMigrationRepairFlow(ConfirmRepairFlow):
    """Repair flow to migrate gruenbeck_softliQ_SC config entries to new domain."""
    
    async def async_step_init(self, user_input=None) -> data_entry_flow.FlowResult:
        """Start the repair flow – go straight to confirmation."""
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None) -> data_entry_flow.FlowResult:
        """Handle the user's confirmation to perform migration."""
        if user_input is not None:
            hass: HomeAssistant = self.hass

            # 1. Gather all old config entries
            old_entries = hass.config_entries.async_entries(DOMAIN)

            # 2. Remove entities from old entries to avoid unique_id conflicts
            ent_reg = er.async_get(hass)
            for entity_entry in list(ent_reg.entities.values()):
                if entity_entry.config_entry_id in {entry.entry_id for entry in old_entries}:
                    ent_reg.async_remove(entity_entry.entity_id)

            # 3. Update device identifiers for each affected device
            dev_reg = dr.async_get(hass)
            for device in list(dev_reg.devices.values()):
                if any(iden[0] == DOMAIN for iden in device.identifiers):
                    new_ids = {
                        (NEW_DOMAIN, iden[1]) if iden[0] == DOMAIN else iden
                        for iden in device.identifiers
                    }
                    dev_reg.async_update_device(device_id=device.id, new_identifiers=new_ids)

            # 4. Create new config entries for each old entry
            for old_entry in list(old_entries):
                new_entry = ConfigEntry(
                    version=old_entry.version,
                    domain=NEW_DOMAIN,
                    title=old_entry.title,
                    data={**old_entry.data},
                    options={**old_entry.options},
                    entry_id=old_entry.entry_id + "_migrated",  # or uuid4
                    source=old_entry.source,
                    unique_id=old_entry.unique_id,
                    discovery_keys= old_entry.discovery_keys,
                    minor_version= old_entry.minor_version,
                    subentries_data=None

                )
                await hass.config_entries.async_add(new_entry)

            # 5. Remove old config entries
            for old_entry in old_entries:
                await hass.config_entries.async_remove(old_entry.entry_id)

            return self.async_create_entry(title="", data={})

        # Prompt for confirmation (no fields, just a message)
        return await super().async_step_confirm(user_input)
      
async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data: dict | None) -> ConfirmRepairFlow| None:
    """Instantiate the repair flow for a given issue."""
    if issue_id == "domain_migration":
        return DomainMigrationRepairFlow()