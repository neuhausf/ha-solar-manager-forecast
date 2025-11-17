"""Constants for the Solar Manager Forecast integration."""

from __future__ import annotations

import logging

DOMAIN = "solar_manager_forecast"
LOGGER = logging.getLogger(__package__)

NAME = "Solar Manager Forecast"
VERSION = "0.1.0"
ATTRIBUTION = "Data provided by Solar Manager (cloud.solar-manager.ch)"

# Config keys
CONF_SMART_MANAGER_ID = "smid"
CONF_BASE_URL = "base_url"          # optional override for the API URL
