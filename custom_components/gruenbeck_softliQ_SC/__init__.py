# custom_components/gruenbeck_softliQ_SC/__init__.py
from homeassistant.helpers import issue_registry as ir
from .const import DOMAIN, NEW_DOMAIN

async def async_setup(hass, config):
    # If any old config entry exists, create a repair issue
    if hass.config_entries.async_entries(DOMAIN):
        ir.async_create_issue(
            hass,
            DOMAIN,
            "domain_migration",  # issue identifier
            is_fixable=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key="domain_migration",
            translation_placeholders={"old_domain": DOMAIN, "new_domain": NEW_DOMAIN}
        )
    return True

async def async_setup_entry(hass, entry):
    # Do not set up old domain entities; just mark setup complete.
    return True