"""Sensor platform for Enhanced Thermostat integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.climate import HVACAction

from .const import (
    DOMAIN,
    CONF_TRACKING_ENABLED,
    ATTR_DAILY_HEATING_HOURS,
    ATTR_DAILY_COOLING_HOURS,
)
from .coordinator import EnhancedThermostatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Enhanced Thermostat sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    if coordinator.get_config_value(CONF_TRACKING_ENABLED, True):
        async_add_entities(
            [
                EnhancedThermostatHeatingHoursSensor(coordinator, entry),
                EnhancedThermostatCoolingHoursSensor(coordinator, entry),
            ],
            True,
        )


class EnhancedThermostatUsageTracker:
    """Track HVAC usage for reporting."""

    def __init__(self) -> None:
        """Initialize the usage tracker."""
        self._heating_start: datetime | None = None
        self._cooling_start: datetime | None = None
        self._daily_heating_seconds: int = 0
        self._daily_cooling_seconds: int = 0
        self._last_reset_date: datetime = datetime.now().date()
        self._history: dict[str, dict[str, float]] = {}

    def update(self, hvac_action: str | None) -> None:
        """Update tracking based on current HVAC action."""
        now = datetime.now()
        
        # Check if we need to reset daily counters
        if now.date() > self._last_reset_date:
            self._save_daily_data()
            self._reset_daily_counters()

        # Update heating tracking
        if hvac_action == HVACAction.HEATING:
            if self._heating_start is None:
                self._heating_start = now
        else:
            if self._heating_start is not None:
                duration = (now - self._heating_start).total_seconds()
                self._daily_heating_seconds += int(duration)
                self._heating_start = None

        # Update cooling tracking
        if hvac_action == HVACAction.COOLING:
            if self._cooling_start is None:
                self._cooling_start = now
        else:
            if self._cooling_start is not None:
                duration = (now - self._cooling_start).total_seconds()
                self._daily_cooling_seconds += int(duration)
                self._cooling_start = None

    def _save_daily_data(self) -> None:
        """Save daily data to history."""
        date_str = self._last_reset_date.isoformat()
        self._history[date_str] = {
            "heating_hours": self._daily_heating_seconds / 3600,
            "cooling_hours": self._daily_cooling_seconds / 3600,
        }
        
        # Keep only last 90 days
        if len(self._history) > 90:
            oldest_date = min(self._history.keys())
            del self._history[oldest_date]

    def _reset_daily_counters(self) -> None:
        """Reset daily counters."""
        self._daily_heating_seconds = 0
        self._daily_cooling_seconds = 0
        self._last_reset_date = datetime.now().date()

    @property
    def daily_heating_hours(self) -> float:
        """Return daily heating hours."""
        return self._daily_heating_seconds / 3600

    @property
    def daily_cooling_hours(self) -> float:
        """Return daily cooling hours."""
        return self._daily_cooling_seconds / 3600

    def get_history(self, days: int = 30) -> dict[str, dict[str, float]]:
        """Get historical data for the last N days."""
        start_date = (datetime.now().date() - timedelta(days=days)).isoformat()
        return {
            date: data
            for date, data in self._history.items()
            if date >= start_date
        }

    def export_csv(self) -> str:
        """Export history as CSV."""
        lines = ["Date,Heating Hours,Cooling Hours"]
        
        for date in sorted(self._history.keys()):
            data = self._history[date]
            lines.append(
                f"{date},{data['heating_hours']:.2f},{data['cooling_hours']:.2f}"
            )
        
        # Add today's data (in progress)
        today = datetime.now().date().isoformat()
        lines.append(
            f"{today},{self.daily_heating_hours:.2f},{self.daily_cooling_hours:.2f}"
        )
        
        return "\n".join(lines)


class EnhancedThermostatHeatingHoursSensor(CoordinatorEntity, SensorEntity):
    """Sensor for daily heating hours."""

    _attr_has_entity_name = True
    _attr_name = "Daily Heating Hours"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:fire"

    def __init__(
        self,
        coordinator: EnhancedThermostatCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_heating_hours"
        self._tracker = EnhancedThermostatUsageTracker()
        
        # Store tracker in coordinator for access by other components
        coordinator.usage_tracker = self._tracker

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

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return round(self._tracker.daily_heating_hours, 2)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data:
            hvac_action = self.coordinator.data["attributes"].get("hvac_action")
            self._tracker.update(hvac_action)
        
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return {
            "last_reset": self._tracker._last_reset_date.isoformat(),
            "history_days": len(self._tracker._history),
        }


class EnhancedThermostatCoolingHoursSensor(CoordinatorEntity, SensorEntity):
    """Sensor for daily cooling hours."""

    _attr_has_entity_name = True
    _attr_name = "Daily Cooling Hours"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:snowflake"

    def __init__(
        self,
        coordinator: EnhancedThermostatCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_cooling_hours"
        
        # Use the same tracker instance from coordinator
        self._tracker = None

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

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        if self._tracker is None:
            self._tracker = getattr(self.coordinator, "usage_tracker", None)
        
        if self._tracker:
            return round(self._tracker.daily_cooling_hours, 2)
        return 0.0

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._tracker is None:
            self._tracker = getattr(self.coordinator, "usage_tracker", None)
        
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self._tracker:
            return {
                "last_reset": self._tracker._last_reset_date.isoformat(),
                "history_days": len(self._tracker._history),
            }
        return {}
