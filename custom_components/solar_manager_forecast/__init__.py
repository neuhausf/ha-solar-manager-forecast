"""The Solar Manager Forecast integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER
from .coordinator import SolarManagerForecastDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Manager Forecast from a config entry."""
    LOGGER.debug("Setting up config entry %s for %s", entry.entry_id, DOMAIN)

    coordinator = SolarManagerForecastDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator under the domain namespace
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Register sensor platform(s)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload the integration when options are changed
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    LOGGER.debug("Unloading config entry %s for %s", entry.entry_id, DOMAIN)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    LOGGER.debug("Options updated for config entry %s, reloading", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)
