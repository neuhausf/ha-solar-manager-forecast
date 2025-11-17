"""Diagnostics support for Solar Manager Forecast integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, CONF_SMART_MANAGER_ID
from .solar_manager_forecast import Estimate

# Fields to be redacted in diagnostics
TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SMART_MANAGER_ID,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: DataUpdateCoordinator[Estimate] = hass.data[DOMAIN][entry.entry_id]
    estimate: Estimate | None = getattr(coordinator, "data", None)

    if estimate is None:
        # No data loaded yet
        return {
            "entry": {
                "title": entry.title,
                "data": async_redact_data(entry.data, TO_REDACT),
                "options": async_redact_data(entry.options, TO_REDACT),
            },
            "data": None,
        }

    return {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": async_redact_data(entry.options, TO_REDACT),
        },
        "data": {
            "power_production_now": estimate.power_production_now,
            "watts": {
                watt_datetime.isoformat(): watt_value
                for watt_datetime, watt_value in estimate.watts.items()
            },
            "wh_period": {
                wh_datetime.isoformat(): wh_value
                for wh_datetime, wh_value in estimate.wh_period.items()
            },
            "wh_hours": {
                wh_datetime.isoformat(): wh_value
                for wh_datetime, wh_value in estimate.wh_hours.items()
            },
        },
        "account": {
            "timezone": str(estimate.timezone),
        },
    }
