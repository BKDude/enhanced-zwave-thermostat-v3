"""Safety temperature monitoring for Enhanced Thermostat."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.climate import HVACMode
from homeassistant.components.persistent_notification import async_create

from .const import (
    CONF_SAFETY_MIN_TEMP,
    CONF_SAFETY_MAX_TEMP,
    CONF_HYSTERESIS,
    DEFAULT_SAFETY_MIN_TEMP,
    DEFAULT_SAFETY_MAX_TEMP,
    DEFAULT_HYSTERESIS,
    NOTIFICATION_ID,
    NOTIFICATION_TITLE,
)

if TYPE_CHECKING:
    from .coordinator import EnhancedThermostatCoordinator
    from .climate import EnhancedThermostatClimate

_LOGGER = logging.getLogger(__name__)


class SafetyMonitor:
    """Monitor and enforce safety temperature limits."""

    def __init__(
        self,
        coordinator: EnhancedThermostatCoordinator,
        climate_entity: EnhancedThermostatClimate,
    ) -> None:
        """Initialize the safety monitor."""
        self.coordinator = coordinator
        self.climate_entity = climate_entity
        self._last_safety_mode: str | None = None

    def check_safety(self) -> None:
        """Check if safety temperature action is needed."""
        if not self.coordinator.data:
            return

        current_temp = self.coordinator.data["attributes"].get("current_temperature")
        hvac_mode = self.coordinator.data.get("state")

        if current_temp is None:
            return

        safety_min = self.coordinator.get_config_value(
            CONF_SAFETY_MIN_TEMP, DEFAULT_SAFETY_MIN_TEMP
        )
        safety_max = self.coordinator.get_config_value(
            CONF_SAFETY_MAX_TEMP, DEFAULT_SAFETY_MAX_TEMP
        )
        hysteresis = self.coordinator.get_config_value(
            CONF_HYSTERESIS, DEFAULT_HYSTERESIS
        )

        # Check if thermostat is off
        if hvac_mode != HVACMode.OFF:
            # If thermostat is on, reset safety state
            if self.coordinator.safety_triggered:
                self.coordinator.safety_triggered = False
                self._last_safety_mode = None
            return

        # Check for dangerous low temperature
        if current_temp < safety_min:
            if not self.coordinator.safety_triggered or self._last_safety_mode != "heat":
                _LOGGER.warning(
                    "Safety temperature triggered: Current temperature %.1f°C is below minimum %.1f°C",
                    current_temp,
                    safety_min,
                )
                self._activate_safety_heating(current_temp, safety_min)

        # Check for dangerous high temperature
        elif current_temp > safety_max:
            if not self.coordinator.safety_triggered or self._last_safety_mode != "cool":
                _LOGGER.warning(
                    "Safety temperature triggered: Current temperature %.1f°C is above maximum %.1f°C",
                    current_temp,
                    safety_max,
                )
                self._activate_safety_cooling(current_temp, safety_max)

        # Check if we can deactivate safety mode (with hysteresis)
        elif self.coordinator.safety_triggered:
            if self._last_safety_mode == "heat" and current_temp >= safety_min + hysteresis:
                _LOGGER.info(
                    "Safety heating deactivated: Temperature %.1f°C is now safe",
                    current_temp,
                )
                self._deactivate_safety()
            elif self._last_safety_mode == "cool" and current_temp <= safety_max - hysteresis:
                _LOGGER.info(
                    "Safety cooling deactivated: Temperature %.1f°C is now safe",
                    current_temp,
                )
                self._deactivate_safety()

    def _activate_safety_heating(self, current_temp: float, safety_min: float) -> None:
        """Activate safety heating mode."""
        self.coordinator.safety_triggered = True
        self._last_safety_mode = "heat"

        # Set thermostat to heat mode with target temperature
        target_temp = safety_min + self.coordinator.get_config_value(
            CONF_HYSTERESIS, DEFAULT_HYSTERESIS
        )

        self.coordinator.hass.async_create_task(
            self.coordinator.hass.services.async_call(
                "climate",
                "set_temperature",
                {
                    "entity_id": self.coordinator.source_entity_id,
                    "hvac_mode": HVACMode.HEAT,
                    "temperature": target_temp,
                },
                blocking=False,
            )
        )

        # Send notification
        message = (
            f"⚠️ Safety temperature alert!\n\n"
            f"Current temperature: {current_temp:.1f}°C\n"
            f"Safety minimum: {safety_min:.1f}°C\n\n"
            f"Thermostat has been automatically set to HEAT mode "
            f"with target temperature {target_temp:.1f}°C."
        )

        async_create(
            self.coordinator.hass,
            message,
            title=NOTIFICATION_TITLE,
            notification_id=f"{NOTIFICATION_ID}_heat",
        )

    def _activate_safety_cooling(self, current_temp: float, safety_max: float) -> None:
        """Activate safety cooling mode."""
        self.coordinator.safety_triggered = True
        self._last_safety_mode = "cool"

        # Set thermostat to cool mode with target temperature
        target_temp = safety_max - self.coordinator.get_config_value(
            CONF_HYSTERESIS, DEFAULT_HYSTERESIS
        )

        self.coordinator.hass.async_create_task(
            self.coordinator.hass.services.async_call(
                "climate",
                "set_temperature",
                {
                    "entity_id": self.coordinator.source_entity_id,
                    "hvac_mode": HVACMode.COOL,
                    "temperature": target_temp,
                },
                blocking=False,
            )
        )

        # Send notification
        message = (
            f"⚠️ Safety temperature alert!\n\n"
            f"Current temperature: {current_temp:.1f}°C\n"
            f"Safety maximum: {safety_max:.1f}°C\n\n"
            f"Thermostat has been automatically set to COOL mode "
            f"with target temperature {target_temp:.1f}°C."
        )

        async_create(
            self.coordinator.hass,
            message,
            title=NOTIFICATION_TITLE,
            notification_id=f"{NOTIFICATION_ID}_cool",
        )

    def _deactivate_safety(self) -> None:
        """Deactivate safety mode and return thermostat to OFF."""
        self.coordinator.safety_triggered = False
        self._last_safety_mode = None

        # Turn thermostat back off
        self.coordinator.hass.async_create_task(
            self.coordinator.hass.services.async_call(
                "climate",
                "set_hvac_mode",
                {
                    "entity_id": self.coordinator.source_entity_id,
                    "hvac_mode": HVACMode.OFF,
                },
                blocking=False,
            )
        )

        # Send notification
        message = (
            "✅ Safety temperature alert resolved!\n\n"
            "Temperature has returned to safe levels. "
            "Thermostat has been returned to OFF mode."
        )

        async_create(
            self.coordinator.hass,
            message,
            title=NOTIFICATION_TITLE,
            notification_id=f"{NOTIFICATION_ID}_resolved",
        )
