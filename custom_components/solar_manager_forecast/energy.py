"""Energy platform for Solar Manager Forecast."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_solar_forecast(
    hass: HomeAssistant, config_entry_id: str
) -> dict[str, dict[str, float]] | None:
    """Get solar forecast for a config entry ID.

    This is used by the Home Assistant Energy dashboard to draw
    the dotted solar forecast line.
    """
    coordinator = hass.data[DOMAIN].get(config_entry_id)
    if coordinator is None:
        return None

    estimate = getattr(coordinator, "data", None)
    if estimate is None:
        return None

    # Expected: estimate.wh_hours = { datetime: Wh, ... }
    wh_hours = getattr(estimate, "wh_hours", None)
    if not wh_hours:
        return None

    return {
        "wh_hours": {
            timestamp.isoformat(): value
            for timestamp, value in wh_hours.items()
        }
    }
