"""Integration platform for recorder."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback


@callback
def exclude_attributes(hass: HomeAssistant) -> set[str]:
    """Exclude attributes from being recorded in the database.

    Currently no attributes are excluded for Solar Manager Forecast.
    """
    return set()
