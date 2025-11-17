"""Config flow for Solar Manager Forecast integration."""
from __future__ import annotations

from typing import Any
import logging

import voluptuous as vol
from voluptuous.schema_builder import Schema

from homeassistant import config_entries
from homeassistant.const import (
    CONF_NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, NAME, CONF_SMART_MANAGER_ID

_LOGGER = logging.getLogger(__name__)


def step_user_data_schema(data: dict[str, Any] | None = None) -> Schema:
    """Build the schema for the user and options forms."""
    # Do not use mutable default arguments
    if data is None:
        data = {}

    _LOGGER.debug("config_flow: building schema with data=%s", data)

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data.get(CONF_NAME, NAME)): str,
            vol.Required(CONF_USERNAME, default=data.get(CONF_USERNAME, "")): str,
            vol.Required(CONF_PASSWORD, default=data.get(CONF_PASSWORD, "")): str,
            vol.Required(
                CONF_SMART_MANAGER_ID,
                default=data.get(CONF_SMART_MANAGER_ID, ""),
            ): str,
        },
        extra=vol.PREVENT_EXTRA,
    )


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input.

    Hier könntest du später einen echten Connectivity-Check
    gegen die Solar-Manager-API mit Basic Auth einbauen.
    """
    _LOGGER.debug("config_flow: validate_input: %s", data)

    # Minimal plausibility checks
    if not data.get(CONF_SMART_MANAGER_ID):
        raise InvalidHost("Smart Manager ID is required")

    # TODO: Optional: Test-Request mit Username/Password + SMID machen.

    # Title that appears in the UI as the name of the entry
    return {"title": data.get(CONF_NAME) or NAME}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solar Manager Forecast."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        _LOGGER.debug(
            "config_flow: async_get_options_flow called for entry_id=%s",
            entry.entry_id,
        )
        return OptionsFlow(entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step of the config flow."""
        _LOGGER.debug("config_flow: async_step_user: user_input=%s", user_input)

        if user_input is None:
            # First call → show form
            return self.async_show_form(
                step_id="user",
                data_schema=step_user_data_schema(),
            )

        errors: dict[str, str] = {}

        try:
            info = await validate_input(self.hass, user_input)
        except InvalidHost:
            errors["base"] = "invalid_host"
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected exception during config flow")
            errors["base"] = "unknown"
        else:
            _LOGGER.debug(
                "config_flow: async_step_user: validation passed: %s", user_input
            )

            # Enforce uniqueness per Smart Manager ID
            await self.async_set_unique_id(user_input[CONF_SMART_MANAGER_ID])
            self._abort_if_unique_id_configured()

            # Credentials & SMID go into data (persistent),
            # additionally, we store everything as options so that the OptionsFlow
            # can show the same defaults.
            return self.async_create_entry(
                title=info["title"],
                data=user_input,
                options=user_input,
            )

        _LOGGER.debug(
            "config_flow: async_step_user: validation failed: %s, errors=%s",
            user_input,
            errors,
        )

        return self.async_show_form(
            step_id="user",
            data_schema=step_user_data_schema(user_input),
            errors=errors,
        )


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options for an existing config entry."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        _LOGGER.debug("config_flow: OptionsFlow.__init__: entry_id=%s", entry.entry_id)
        self.entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        _LOGGER.debug("config_flow: OptionsFlow.async_step_init: %s", user_input)

        if user_input is None:
            # Existing options or fallback to data as defaults
            defaults = {**self.entry.data, **self.entry.options}
            return self.async_show_form(
                step_id="init",
                data_schema=step_user_data_schema(defaults),
            )

        errors: dict[str, str] = {}

        try:
            info = await validate_input(self.hass, user_input)
        except InvalidHost:
            errors["base"] = "invalid_host"
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected exception during options flow")
            errors["base"] = "unknown"
        else:
            # Only update options – data remains unchanged.
            return self.async_create_entry(
                title=info["title"],
                data=user_input,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=step_user_data_schema(user_input),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate invalid Smart Manager ID or configuration."""
