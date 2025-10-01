"""Climate platform for Enhanced Thermostat integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
    PRECISION_TENTHS,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_SOURCE_ENTITY,
    CONF_SAFETY_ENABLED,
    CONF_SAFETY_MIN_TEMP,
    CONF_SAFETY_MAX_TEMP,
    CONF_HYSTERESIS,
    CONF_SCHEDULE_ENABLED,
    DEFAULT_SAFETY_MIN_TEMP,
    DEFAULT_SAFETY_MAX_TEMP,
    DEFAULT_HYSTERESIS,
    ATTR_SAFETY_ACTIVE,
    ATTR_SCHEDULE_ACTIVE,
    ATTR_NEXT_SCHEDULE_EVENT,
    ATTR_OVERRIDE_UNTIL,
)
from .coordinator import EnhancedThermostatCoordinator
from .scheduler import ThermostatScheduler
from .safety import SafetyMonitor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Enhanced Thermostat climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities(
        [EnhancedThermostatClimate(coordinator, entry)],
        True,
    )


class EnhancedThermostatClimate(CoordinatorEntity, ClimateEntity):
    """Representation of an Enhanced Thermostat."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = PRECISION_TENTHS

    def __init__(
        self,
        coordinator: EnhancedThermostatCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the thermostat."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_climate"
        
        # Initialize scheduler and safety monitor
        self._scheduler = ThermostatScheduler(coordinator)
        self._safety_monitor = SafetyMonitor(coordinator, self)
        
        # Get source entity state to initialize features
        self._update_from_source()

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Enhanced Thermostat",
            "model": "Z-Wave Thermostat Companion",
            "sw_version": "1.0.0",
        }

    @callback
    def _update_from_source(self) -> None:
        """Update thermostat state from source entity."""
        if not self.coordinator.data:
            return
            
        source_state = self.coordinator.data.get("state")
        source_attrs = self.coordinator.data.get("attributes", {})
        
        # Copy basic attributes
        self._attr_current_temperature = source_attrs.get("current_temperature")
        self._attr_target_temperature = source_attrs.get("temperature")
        self._attr_target_temperature_high = source_attrs.get("target_temp_high")
        self._attr_target_temperature_low = source_attrs.get("target_temp_low")
        
        # Copy HVAC mode
        try:
            self._attr_hvac_mode = HVACMode(source_state) if source_state else HVACMode.OFF
        except ValueError:
            self._attr_hvac_mode = HVACMode.OFF
        
        # Copy HVAC action
        hvac_action = source_attrs.get("hvac_action")
        if hvac_action:
            try:
                self._attr_hvac_action = HVACAction(hvac_action)
            except ValueError:
                self._attr_hvac_action = None
        
        # Copy supported features and modes
        self._attr_hvac_modes = source_attrs.get("hvac_modes", [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL])
        self._attr_preset_modes = source_attrs.get("preset_modes", [])
        self._attr_preset_mode = source_attrs.get("preset_mode")
        self._attr_fan_modes = source_attrs.get("fan_modes", [])
        self._attr_fan_mode = source_attrs.get("fan_mode")
        self._attr_swing_modes = source_attrs.get("swing_modes", [])
        self._attr_swing_mode = source_attrs.get("swing_mode")
        
        # Temperature limits
        self._attr_max_temp = source_attrs.get("max_temp", 35)
        self._attr_min_temp = source_attrs.get("min_temp", 7)
        self._attr_target_temperature_step = source_attrs.get("target_temp_step", 0.5)
        
        # Determine supported features
        features = ClimateEntityFeature(0)
        if self._attr_target_temperature is not None:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self._attr_target_temperature_high is not None and self._attr_target_temperature_low is not None:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        if self._attr_preset_modes:
            features |= ClimateEntityFeature.PRESET_MODE
        if self._attr_fan_modes:
            features |= ClimateEntityFeature.FAN_MODE
        if self._attr_swing_modes:
            features |= ClimateEntityFeature.SWING_MODE
        
        self._attr_supported_features = features

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_from_source()
        
        # Check scheduler
        if self.coordinator.get_config_value(CONF_SCHEDULE_ENABLED, True):
            self._scheduler.check_schedule()
        
        # Check safety monitor
        if self.coordinator.get_config_value(CONF_SAFETY_ENABLED, True):
            self._safety_monitor.check_safety()
        
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {}
        
        # Safety attributes
        if self.coordinator.get_config_value(CONF_SAFETY_ENABLED, True):
            attrs[ATTR_SAFETY_ACTIVE] = self.coordinator.safety_triggered
            attrs["safety_min_temp"] = self.coordinator.get_config_value(
                CONF_SAFETY_MIN_TEMP, DEFAULT_SAFETY_MIN_TEMP
            )
            attrs["safety_max_temp"] = self.coordinator.get_config_value(
                CONF_SAFETY_MAX_TEMP, DEFAULT_SAFETY_MAX_TEMP
            )
        
        # Schedule attributes
        if self.coordinator.get_config_value(CONF_SCHEDULE_ENABLED, True):
            next_event = self._scheduler.get_next_event()
            attrs[ATTR_SCHEDULE_ACTIVE] = next_event is not None
            attrs[ATTR_NEXT_SCHEDULE_EVENT] = next_event
        
        # Override attributes
        if self.coordinator.override_until:
            attrs[ATTR_OVERRIDE_UNTIL] = self.coordinator.override_until
        
        return attrs

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        target_temp_high = kwargs.get("target_temp_high")
        target_temp_low = kwargs.get("target_temp_low")
        hvac_mode = kwargs.get("hvac_mode")
        
        service_data = {
            "entity_id": self.coordinator.source_entity_id,
        }
        
        if temperature is not None:
            service_data[ATTR_TEMPERATURE] = temperature
        if target_temp_high is not None:
            service_data["target_temp_high"] = target_temp_high
        if target_temp_low is not None:
            service_data["target_temp_low"] = target_temp_low
        if hvac_mode is not None:
            service_data["hvac_mode"] = hvac_mode
        
        await self.hass.services.async_call(
            "climate",
            "set_temperature",
            service_data,
            blocking=True,
        )
        
        # Set override until next scheduled event
        if self.coordinator.get_config_value(CONF_SCHEDULE_ENABLED, True):
            next_event = self._scheduler.get_next_event()
            if next_event:
                self.coordinator.override_until = next_event["time"]

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        await self.hass.services.async_call(
            "climate",
            "set_hvac_mode",
            {
                "entity_id": self.coordinator.source_entity_id,
                "hvac_mode": hvac_mode,
            },
            blocking=True,
        )
        
        # Set override until next scheduled event
        if self.coordinator.get_config_value(CONF_SCHEDULE_ENABLED, True):
            next_event = self._scheduler.get_next_event()
            if next_event:
                self.coordinator.override_until = next_event["time"]

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        await self.hass.services.async_call(
            "climate",
            "set_preset_mode",
            {
                "entity_id": self.coordinator.source_entity_id,
                "preset_mode": preset_mode,
            },
            blocking=True,
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self.hass.services.async_call(
            "climate",
            "set_fan_mode",
            {
                "entity_id": self.coordinator.source_entity_id,
                "fan_mode": fan_mode,
            },
            blocking=True,
        )

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        await self.hass.services.async_call(
            "climate",
            "set_swing_mode",
            {
                "entity_id": self.coordinator.source_entity_id,
                "swing_mode": swing_mode,
            },
            blocking=True,
        )
