"""Support for the SoftQLink sensor service."""
from __future__ import annotations

from dataclasses import dataclass
import logging


from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONTENT_TYPE_TEXT_PLAIN,
    PERCENTAGE,
    EntityCategory,
    UnitOfMass,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
    UnitOfElectricCurrent
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SoftQLinkDataUpdateCoordinator
from .const import DOMAIN, TOTAL_CONSUMPTION

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 1


@dataclass(frozen=True)
class SoftQLinkSensorEntityDescription(SensorEntityDescription):
    """Class describing SoftQLink sensor entities."""



SENSOR_TYPES: tuple[SoftQLinkSensorEntityDescription, ...] = (
    # current flow
    SoftQLinkSensorEntityDescription(
        key="D_A_1_1",
        translation_key="D_A_1_1",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=None,
    ),
    # calculated by current flow
    SoftQLinkSensorEntityDescription(
        key=TOTAL_CONSUMPTION,
        translation_key=TOTAL_CONSUMPTION,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.WATER,
        entity_category=None,
    ),
    # remaining capacity
    SoftQLinkSensorEntityDescription(
        key="D_A_1_2",
        translation_key="D_A_1_2",
        native_unit_of_measurement="m³*°dH",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Capacity number
    SoftQLinkSensorEntityDescription(
        key="D_A_1_3",
        translation_key="D_A_1_3",
        native_unit_of_measurement="m³*°dH",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Total flow
    SoftQLinkSensorEntityDescription(
        key="D_A_1_7",
        translation_key="D_A_1_7",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WATER,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # Remaining time/quantity regeneration step
    SoftQLinkSensorEntityDescription(
        key="D_A_2_1",
        translation_key="D_A_2_1",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # days until the next maintenance
    SoftQLinkSensorEntityDescription(
        key="D_A_2_2",
        translation_key="D_A_2_2",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Salt range in days
    SoftQLinkSensorEntityDescription(
        key="D_A_2_3",
        translation_key="D_A_2_3",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Last regeneration
    SoftQLinkSensorEntityDescription(
        key="D_A_3_1",
        translation_key="D_A_3_1",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Percentage regeneration
    SoftQLinkSensorEntityDescription(
        key="D_A_3_2",
        translation_key="D_A_3_2",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Raw water hardness
    SoftQLinkSensorEntityDescription(
        key="D_D_1",
        translation_key="D_D_1",
        native_unit_of_measurement="°dH",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Soft water volume meter
    SoftQLinkSensorEntityDescription(
        key="D_K_2",
        translation_key="D_K_2",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.WATER,
    ),
    # Flow peak value
    SoftQLinkSensorEntityDescription(
        key="D_K_3",
        translation_key="D_K_3",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Chlorstrom
    SoftQLinkSensorEntityDescription(
        key="D_K_5",
        translation_key="D_K_5",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Consumption capacity rate
    SoftQLinkSensorEntityDescription(
        key="D_K_8",
        translation_key="D_K_8",
        native_unit_of_measurement="m³*°dH",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Average consumption over the last 3 day
    SoftQLinkSensorEntityDescription(
        key="D_K_9",
        translation_key="D_K_9",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Last error code
    SoftQLinkSensorEntityDescription(
        key="D_K_10_1",
        translation_key="D_K_10_1",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Last error code days old
    SoftQLinkSensorEntityDescription(
        key="D_K_10_1_Hours",
        translation_key="D_K_10_1_Hours",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Water consumption yesterday
    SoftQLinkSensorEntityDescription(
        key="D_Y_1",
        translation_key="D_Y_1",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Salt consumption per year
    SoftQLinkSensorEntityDescription(
        key="D_Y_3",
        translation_key="D_Y_3",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # Current regeneration step
    SoftQLinkSensorEntityDescription(
        key="D_Y_5", translation_key="D_Y_5", entity_category=EntityCategory.DIAGNOSTIC
    ),
    # software version
    SoftQLinkSensorEntityDescription(
        key="D_Y_6",
        translation_key="D_Y_6",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up SoftQLink sensor entities based on a config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.info(coordinator.data)
    sensors = []
    for description in SENSOR_TYPES:
        # When we use the nearest method, we are not sure which sensors are available
        _LOGGER.info(description.key)
        sensors.append(SoftQLinkSensor(coordinator, description))

    async_add_entities(sensors, False)


class SoftQLinkSensor(CoordinatorEntity[SoftQLinkDataUpdateCoordinator], SensorEntity): # type: ignore
    """Define an SoftQLink sensor."""

    _attr_attribution = "Data from SoftQLink"
    _attr_has_entity_name = True
    entity_description: SoftQLinkSensorEntityDescription

    def __init__(
        self,
        coordinator: SoftQLinkDataUpdateCoordinator,
        description: SoftQLinkSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.name}")},
            name=coordinator.name,
            manufacturer="Gruenbeck",
            model=coordinator.clientMuxClient.model,
            sw_version=coordinator.clientMuxClient.sw_version,
        )
        self._attr_unique_id = f"{coordinator.name}-{description.key}".lower()
        if description.key in coordinator.data:
            val = coordinator.data.get(description.key)
            if val != "-":
                self._attr_native_value = val
        self.entity_description = description # type: ignore

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.entity_description.key in self.coordinator.data:
            val = self.coordinator.data.get(self.entity_description.key)
            if val != "-":
                self._attr_native_value = val
        self.async_write_ha_state()
