"""Support for the Solar Manager Forecast sensor service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .solar_manager_forecast import Estimate
from .const import DOMAIN
from .coordinator import SolarManagerForecastDataUpdateCoordinator


@dataclass(frozen=True)
class SolarManagerForecastSensorEntityDescription(SensorEntityDescription):
    """Describes a Solar Manager Forecast sensor."""

    state: Callable[[Estimate], Any] | None = None


def _power_production_next_24h_15min(estimate: Estimate) -> list[int]:
    """Return estimated power production for the next 24 h in 15-min intervals (96 values)."""
    now = estimate.now()
    return [
        estimate.power_production_at_time(now + timedelta(minutes=15 * i))
        for i in range(96)  # 96 = 24 hours * 4 intervals per hour
    ]


# Minimal set of sensors – only power, energy sensors are
# estimated and provided by solar_manager_forecast.py.
SENSORS: tuple[SolarManagerForecastSensorEntityDescription, ...] = (
    SolarManagerForecastSensorEntityDescription(
        key="power_production_now",
        translation_key="power_production_now",
        device_class=SensorDeviceClass.POWER,
        state=lambda estimate: estimate.power_production_now,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SolarManagerForecastSensorEntityDescription(
        key="power_production_next_15minutes",
        translation_key="power_production_next_15minutes",
        device_class=SensorDeviceClass.POWER,
        state=lambda estimate: estimate.power_production_at_time(
            estimate.now() + timedelta(minutes=15)
        ),
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SolarManagerForecastSensorEntityDescription(
        key="power_production_next_30minutes",
        translation_key="power_production_next_30minutes",
        device_class=SensorDeviceClass.POWER,
        state=lambda estimate: estimate.power_production_at_time(
            estimate.now() + timedelta(minutes=30)
        ),
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SolarManagerForecastSensorEntityDescription(
        key="power_production_next_24h_15min",
        translation_key="power_production_next_24h_15min",
        device_class=SensorDeviceClass.POWER,
        state=lambda estimate: estimate.power_production_now,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Solar Manager Forecast sensors."""
    coordinator: SolarManagerForecastDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    async_add_entities(
        SolarManagerForecastSensorEntity(
            entry_id=entry.entry_id,
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in SENSORS
    )


class SolarManagerForecastSensorEntity(
    CoordinatorEntity[SolarManagerForecastDataUpdateCoordinator], SensorEntity
):
    """Defines a Solar Manager Forecast sensor."""

    entity_description: SolarManagerForecastSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        *,
        entry_id: str,
        coordinator: SolarManagerForecastDataUpdateCoordinator,
        entity_description: SolarManagerForecastSensorEntityDescription,
    ) -> None:
        """Initialize Solar Manager Forecast sensor."""
        super().__init__(coordinator=coordinator)
        self.entity_description = entity_description
        # Fixed entity_id to ensure it remains stable
        self.entity_id = f"{SENSOR_DOMAIN}.{entity_description.key}"
        self._attr_unique_id = f"{entry_id}_{entity_description.key}"

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="Solar Manager",
            name="Solar production forecast",
            configuration_url="https://solarmanager.ch",
        )

    async def _update_callback(self, now: datetime) -> None:
        """Update the entity without fetching data from the server.

        The forecast data is available in 15-minute intervals,
        and the coordinator polls e.g. every 30 minutes. To ensure
        that 'now' & 'next 15/30 minutes' still update correctly,
        we write the state every minute.
        """
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()

        # Update the state of the sensors every minute (without a new API call)
        async_track_utc_time_change(
            self.hass,
            self._update_callback,
            second=0,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes for the sensor."""
        if self.entity_description.key == "power_production_next_24h_15min":
            estimate = self.coordinator.data
            return {"forecasts": _power_production_next_24h_15min(estimate)}
        return None

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        estimate = self.coordinator.data

        if self.entity_description.state is None:
            # Fallback: Attribute with the same name as key on the Estimate object
            return getattr(estimate, self.entity_description.key)
        return self.entity_description.state(estimate)
