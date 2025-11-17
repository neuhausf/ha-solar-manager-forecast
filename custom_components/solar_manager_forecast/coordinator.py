"""DataUpdateCoordinator for the Solar Manager Forecast integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .solar_manager_forecast import (
    Estimate,
    SolarManagerForecastError,
    SolarManagerSolarForecast,
)

from .const import (
    CONF_SMART_MANAGER_ID,
    CONF_BASE_URL,
    DOMAIN,
    LOGGER,
)

UPDATE_INTERVAL: Final = timedelta(minutes=30)


class SolarManagerForecastDataUpdateCoordinator(DataUpdateCoordinator[Estimate]):
    """The Solar Manager Forecast Data Update Coordinator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the Solar Manager Forecast coordinator."""
        self.config_entry = entry

        # Solar Manager ID
        smart_manager_id: str | None = (
            entry.options.get(CONF_SMART_MANAGER_ID)
            or entry.data.get(CONF_SMART_MANAGER_ID)
        )

        # Determine base URL
        if smart_manager_id:
            base_url = (
                f"https://cloud.solar-manager.ch/"
                f"v3/users/{smart_manager_id}/data/forecast"
            )
        else:
            base_url = entry.options.get(CONF_BASE_URL) if entry.options else None

        if not base_url:
            LOGGER.error(
                "No Smart Manager ID or base_url configured for %s",
                entry.title,
            )

        # Username/Password for Basic Auth
        username: str | None = (
            entry.options.get(CONF_USERNAME) or entry.data.get(CONF_USERNAME)
        )
        password: str | None = (
            entry.options.get(CONF_PASSWORD) or entry.data.get(CONF_PASSWORD)
        )

        tz = dt_util.get_time_zone(hass.config.time_zone)

        self.forecast = SolarManagerSolarForecast(
            session=async_get_clientsession(hass),
            base_url=base_url,
            smart_manager_id=smart_manager_id,
            timezone=tz,
            username=username,
            password=password,
        )

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> Estimate:
        """Fetch Solar Manager Forecast estimates."""
        try:
            return await self.forecast.estimate()
        except SolarManagerForecastError as err:
            raise UpdateFailed(
                f"Error communicating with Solar Manager Forecast API: {err}"
            ) from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(
                f"Unexpected error while updating Solar Manager forecast: {err}"
            ) from err
