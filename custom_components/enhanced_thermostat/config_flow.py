"""Config flow for Enhanced Thermostat integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN

from .const import (
    DOMAIN,
    CONF_SOURCE_ENTITY,
    CONF_SAFETY_MIN_TEMP,
    CONF_SAFETY_MAX_TEMP,
    CONF_SAFETY_ENABLED,
    CONF_HYSTERESIS,
    CONF_SCHEDULE_ENABLED,
    CONF_TRACKING_ENABLED,
    DEFAULT_SAFETY_MIN_TEMP,
    DEFAULT_SAFETY_MAX_TEMP,
    DEFAULT_HYSTERESIS,
    DEFAULT_SAFETY_ENABLED,
    DEFAULT_SCHEDULE_ENABLED,
    DEFAULT_TRACKING_ENABLED,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    source_entity = data[CONF_SOURCE_ENTITY]
    
    # Check if entity exists and is a climate entity
    state = hass.states.get(source_entity)
    if state is None:
        raise ValueError("invalid_entity")
    
    if not source_entity.startswith("climate."):
        raise ValueError("invalid_entity")
    
    # Validate temperature range if safety is enabled
    if data.get(CONF_SAFETY_ENABLED, True):
        if data[CONF_SAFETY_MAX_TEMP] <= data[CONF_SAFETY_MIN_TEMP]:
            raise ValueError("invalid_temp_range")
    
    return {"title": data.get(CONF_NAME, f"Enhanced {state.name}")}


class EnhancedThermostatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Enhanced Thermostat."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_SOURCE_ENTITY])
                self._abort_if_unique_id_configured()

                # Store data for next step
                self._data.update(user_input)
                return await self.async_step_safety()

            except ValueError as err:
                errors["base"] = str(err)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"

        # Get all climate entities
        entity_registry = er.async_get(self.hass)
        climate_entities = [
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.domain == CLIMATE_DOMAIN
        ]
        
        # Also include climate entities from states
        for state in self.hass.states.async_all(CLIMATE_DOMAIN):
            if state.entity_id not in climate_entities:
                climate_entities.append(state.entity_id)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=CLIMATE_DOMAIN)
                ),
                vol.Optional(CONF_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_safety(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the safety configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate temperature range if safety is enabled
                if user_input.get(CONF_SAFETY_ENABLED, True):
                    if user_input[CONF_SAFETY_MAX_TEMP] <= user_input[CONF_SAFETY_MIN_TEMP]:
                        errors["base"] = "invalid_temp_range"
                    else:
                        self._data.update(user_input)
                        return await self.async_step_features()
                else:
                    self._data.update(user_input)
                    return await self.async_step_features()

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SAFETY_ENABLED,
                    default=DEFAULT_SAFETY_ENABLED,
                ): bool,
                vol.Optional(
                    CONF_SAFETY_MIN_TEMP,
                    default=DEFAULT_SAFETY_MIN_TEMP,
                ): vol.All(vol.Coerce(float), vol.Range(min=-10, max=40)),
                vol.Optional(
                    CONF_SAFETY_MAX_TEMP,
                    default=DEFAULT_SAFETY_MAX_TEMP,
                ): vol.All(vol.Coerce(float), vol.Range(min=-10, max=50)),
                vol.Optional(
                    CONF_HYSTERESIS,
                    default=DEFAULT_HYSTERESIS,
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=5.0)),
            }
        )

        return self.async_show_form(
            step_id="safety",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_features(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the features configuration step."""
        if user_input is not None:
            self._data.update(user_input)
            
            # Validate the complete configuration
            info = await validate_input(self.hass, self._data)
            
            return self.async_create_entry(
                title=info["title"],
                data=self._data,
            )

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCHEDULE_ENABLED,
                    default=DEFAULT_SCHEDULE_ENABLED,
                ): bool,
                vol.Optional(
                    CONF_TRACKING_ENABLED,
                    default=DEFAULT_TRACKING_ENABLED,
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="features",
            data_schema=data_schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EnhancedThermostatOptionsFlow:
        """Get the options flow for this handler."""
        return EnhancedThermostatOptionsFlow()


class EnhancedThermostatOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Enhanced Thermostat."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate temperature range if safety is enabled
                if user_input.get(CONF_SAFETY_ENABLED, True):
                    if user_input[CONF_SAFETY_MAX_TEMP] <= user_input[CONF_SAFETY_MIN_TEMP]:
                        errors["base"] = "invalid_temp_range"
                    else:
                        return self.async_create_entry(title="", data=user_input)
                else:
                    return self.async_create_entry(title="", data=user_input)

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"

        current_config = {**self.config_entry.data, **self.config_entry.options}

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SAFETY_ENABLED,
                    default=current_config.get(CONF_SAFETY_ENABLED, DEFAULT_SAFETY_ENABLED),
                ): bool,
                vol.Optional(
                    CONF_SAFETY_MIN_TEMP,
                    default=current_config.get(CONF_SAFETY_MIN_TEMP, DEFAULT_SAFETY_MIN_TEMP),
                ): vol.All(vol.Coerce(float), vol.Range(min=-10, max=40)),
                vol.Optional(
                    CONF_SAFETY_MAX_TEMP,
                    default=current_config.get(CONF_SAFETY_MAX_TEMP, DEFAULT_SAFETY_MAX_TEMP),
                ): vol.All(vol.Coerce(float), vol.Range(min=-10, max=50)),
                vol.Optional(
                    CONF_HYSTERESIS,
                    default=current_config.get(CONF_HYSTERESIS, DEFAULT_HYSTERESIS),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=5.0)),
                vol.Optional(
                    CONF_SCHEDULE_ENABLED,
                    default=current_config.get(CONF_SCHEDULE_ENABLED, DEFAULT_SCHEDULE_ENABLED),
                ): bool,
                vol.Optional(
                    CONF_TRACKING_ENABLED,
                    default=current_config.get(CONF_TRACKING_ENABLED, DEFAULT_TRACKING_ENABLED),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
