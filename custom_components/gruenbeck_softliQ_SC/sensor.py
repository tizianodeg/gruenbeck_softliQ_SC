"""Support for the SoftQLink sensor service."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
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
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SoftQLinkDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 1


@dataclass(frozen=True)
class SoftQLinkSensorEntityDescription(SensorEntityDescription):
    """Class describing SoftQLink sensor entities."""

    attrs: Callable[[dict[str, Any]], dict[str, Any]] = lambda data: {}

SENSOR_TYPES: tuple[SoftQLinkSensorEntityDescription, ...] = (
     SoftQLinkSensorEntityDescription(
        key="D_A_1_1",
        translation_key="D_A_1_1",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_A_1_2",
        translation_key="D_A_1_2",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_A_1_3",
        translation_key="D_A_1_3",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_A_1_7",
        translation_key="D_A_1_7",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_A_2_1",
        translation_key="D_A_2_1",
        native_unit_of_measurement= UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_A_2_2",
        translation_key="D_A_2_2",
        native_unit_of_measurement= UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_A_2_3",
        translation_key="D_A_2_3",
        native_unit_of_measurement= UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_A_3_1",
        translation_key="D_A_3_1",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_A_3_2",
        translation_key="D_A_3_2",
        native_unit_of_measurement= PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_Y_1",
        translation_key="D_Y_1",
        native_unit_of_measurement= UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_Y_3",
        translation_key="D_Y_3",
        native_unit_of_measurement= UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
     SoftQLinkSensorEntityDescription(
        key="D_Y_6",
        translation_key="D_Y_6",
        unit_of_measurement= CONTENT_TYPE_TEXT_PLAIN,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
     SoftQLinkSensorEntityDescription(
        key="D_K_2",
        translation_key="D_K_2",
        native_unit_of_measurement= UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ), SoftQLinkSensorEntityDescription(
        key="D_K_3",
        translation_key="D_K_3",
        native_unit_of_measurement= UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ), SoftQLinkSensorEntityDescription(
        key="D_K_8",
        translation_key="D_K_8",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_K_9",
        translation_key="D_K_9",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_D_1",
        translation_key="D_D_1",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC
    ),
     SoftQLinkSensorEntityDescription(
        key="D_Y_5",
        translation_key="D_Y_5",
        entity_category=EntityCategory.DIAGNOSTIC
    ),SoftQLinkSensorEntityDescription(
        key="D_K_10_1",
        translation_key="D_K_10_1",
        entity_category=EntityCategory.DIAGNOSTIC
    ),
    SoftQLinkSensorEntityDescription(
        key="D_K_10_1_Days",
        translation_key="D_K_10_1_Days",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement= UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC
    )
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


class SoftQLinkSensor(CoordinatorEntity[SoftQLinkDataUpdateCoordinator], SensorEntity):
    """Define an Airly sensor."""

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
            model= coordinator.clientMuxClient.model,
            sw_version= coordinator.clientMuxClient.sw_version

        )
        self._attr_unique_id = f"{coordinator.name}-{description.key}".lower()
        if description.key in coordinator.data:
            val = coordinator.data.get(description.key)
            if val != '-':
                self._attr_native_value = val
        self._attr_extra_state_attributes = description.attrs(coordinator.data)
        self.entity_description = description

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.entity_description.key in self.coordinator.data:
            val = self.coordinator.data.get(self.entity_description.key)
            if val != '-':
                self._attr_native_value = val
        self._attr_extra_state_attributes = self.entity_description.attrs(
            self.coordinator.data
        )
        self.async_write_ha_state()
