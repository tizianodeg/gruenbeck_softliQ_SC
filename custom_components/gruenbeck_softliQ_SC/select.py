from typing import Final
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import ( 
    SensorDeviceClass, 
)
from custom_components.gruenbeck_softliQ_SC.const import DOMAIN
from custom_components.gruenbeck_softliQ_SC.coordinator import SoftQLinkDataUpdateCoordinator
from custom_components.gruenbeck_softliQ_SC.sensor import SoftQLinkSensor, SoftQLinkSensorEntityDescription


class SoftQLinkSelectEntityDescription(
    SoftQLinkSensorEntityDescription,
    SelectEntityDescription
):
    """Base class for a Softliq select entity description."""

SELECT_DESCRIPTIONS: Final = [
    SoftQLinkSelectEntityDescription(
        key="D_C_5_1",
        translation_key="D_C_5_1",
        entity_category=None,
        device_class= SensorDeviceClass.ENUM,
        options=[
            "0",
            "1"
        ],
    ),
    
]
SELECT_DESCRIPTIONS_MAP = {desc.key: desc for desc in SELECT_DESCRIPTIONS}



async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    selects = []
    for description in SELECT_DESCRIPTIONS:
         selects.append(SoftQLinkSelectEntity(coordinator, description))
    async_add_entities(selects)


class SoftQLinkSelectEntity(SoftQLinkSensor,SelectEntity): # type: ignore
    """Representation of a tplink select entity."""

    entity_description: SoftQLinkSelectEntityDescription
    _attr_has_entity_name = True
  
    def __init__(
        self, 
        coordinator: SoftQLinkDataUpdateCoordinator, 
        description: SoftQLinkSelectEntityDescription, 
    ) -> None:
        """Initialize a select."""
        super().__init__(
            coordinator
            ,description
        )
        self.entity_description = description # type: ignore
        self._attr_unique_id = f"{coordinator.name}-{description.key}".lower()
   
    
     
    async def async_select_option(self, option: str) -> None:
        """Update the current selected option."""
        await self.coordinator.clientMuxClient.setMode(option) 

    @callback
    def _async_update_attrs(self) -> bool:
        """Update the entity's attributes."""
        if self.entity_description.key in self.coordinator.data:
            self._attr_current_option = self.coordinator.data.get(self.entity_description.key) 
        return True