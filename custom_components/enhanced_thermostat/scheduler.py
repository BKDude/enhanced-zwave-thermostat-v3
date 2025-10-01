"""Scheduler for Enhanced Thermostat."""
from __future__ import annotations

from datetime import datetime, time, timedelta
import logging
from typing import Any, TYPE_CHECKING

from homeassistant.components.climate import HVACMode

from .const import DAYS_OF_WEEK

if TYPE_CHECKING:
    from .coordinator import EnhancedThermostatCoordinator

_LOGGER = logging.getLogger(__name__)


class ThermostatScheduler:
    """Manage thermostat scheduling."""

    def __init__(self, coordinator: EnhancedThermostatCoordinator) -> None:
        """Initialize the scheduler."""
        self.coordinator = coordinator
        self._last_executed: datetime | None = None

    def check_schedule(self) -> None:
        """Check if a scheduled action should be executed."""
        # Check if override is active
        if self.coordinator.override_until:
            override_time = datetime.fromisoformat(self.coordinator.override_until)
            if datetime.now() < override_time:
                _LOGGER.debug("Schedule check skipped: Override active until %s", override_time)
                return
            else:
                # Clear expired override
                self.coordinator.override_until = None

        # Get current day and time
        now = datetime.now()
        current_day = DAYS_OF_WEEK[now.weekday()]
        current_time = now.time()

        # Get schedule for current day
        day_schedule = self.coordinator.schedule_data.get(current_day, [])
        
        if not day_schedule:
            return

        # Find the most recent schedule event that should have triggered
        current_event = None
        for event in sorted(day_schedule, key=lambda x: self._parse_time(x["time"])):
            event_time = self._parse_time(event["time"])
            if event_time <= current_time:
                current_event = event
            else:
                break

        if not current_event:
            return

        # Check if we need to execute this event
        event_datetime = datetime.combine(now.date(), self._parse_time(current_event["time"]))
        
        # Only execute if we haven't executed this event yet today
        if self._last_executed is None or event_datetime > self._last_executed:
            self._execute_schedule_event(current_event)
            self._last_executed = event_datetime

    def _execute_schedule_event(self, event: dict[str, Any]) -> None:
        """Execute a scheduled event."""
        _LOGGER.info("Executing scheduled event: %s", event)

        hvac_mode = event.get("mode", HVACMode.OFF)
        temperature = event.get("temperature")

        service_data = {
            "entity_id": self.coordinator.source_entity_id,
            "hvac_mode": hvac_mode,
        }

        if temperature is not None and hvac_mode != HVACMode.OFF:
            service_data["temperature"] = temperature

        self.coordinator.hass.async_create_task(
            self.coordinator.hass.services.async_call(
                "climate",
                "set_temperature",
                service_data,
                blocking=False,
            )
        )

    def get_next_event(self) -> dict[str, Any] | None:
        """Get the next scheduled event."""
        now = datetime.now()
        current_day_index = now.weekday()
        current_time = now.time()

        # Check remaining events today
        current_day = DAYS_OF_WEEK[current_day_index]
        day_schedule = self.coordinator.schedule_data.get(current_day, [])
        
        for event in sorted(day_schedule, key=lambda x: self._parse_time(x["time"])):
            event_time = self._parse_time(event["time"])
            if event_time > current_time:
                return {
                    "day": current_day,
                    "time": datetime.combine(now.date(), event_time).isoformat(),
                    "mode": event.get("mode", HVACMode.OFF),
                    "temperature": event.get("temperature"),
                }

        # Check next 7 days
        for days_ahead in range(1, 8):
            check_day_index = (current_day_index + days_ahead) % 7
            check_day = DAYS_OF_WEEK[check_day_index]
            day_schedule = self.coordinator.schedule_data.get(check_day, [])
            
            if day_schedule:
                # Get first event of the day
                first_event = min(day_schedule, key=lambda x: self._parse_time(x["time"]))
                event_date = now.date() + timedelta(days=days_ahead)
                event_time = self._parse_time(first_event["time"])
                
                return {
                    "day": check_day,
                    "time": datetime.combine(event_date, event_time).isoformat(),
                    "mode": first_event.get("mode", HVACMode.OFF),
                    "temperature": first_event.get("temperature"),
                }

        return None

    @staticmethod
    def _parse_time(time_str: str) -> time:
        """Parse time string to time object."""
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            _LOGGER.error("Invalid time format: %s", time_str)
            return time(0, 0)

    def set_schedule(self, day: str, events: list[dict[str, Any]]) -> None:
        """Set schedule for a specific day."""
        if day not in DAYS_OF_WEEK:
            _LOGGER.error("Invalid day: %s", day)
            return

        # Validate events
        validated_events = []
        for event in events:
            if "time" not in event or "mode" not in event:
                _LOGGER.error("Invalid event format: %s", event)
                continue
            
            # Validate time format
            try:
                self._parse_time(event["time"])
            except Exception:
                _LOGGER.error("Invalid time in event: %s", event)
                continue

            validated_events.append(event)

        self.coordinator.schedule_data[day] = validated_events
        _LOGGER.info("Schedule set for %s: %s", day, validated_events)

    def clear_schedule(self, day: str | None = None) -> None:
        """Clear schedule for a specific day or all days."""
        if day is None:
            self.coordinator.schedule_data = {}
            _LOGGER.info("All schedules cleared")
        elif day in DAYS_OF_WEEK:
            self.coordinator.schedule_data.pop(day, None)
            _LOGGER.info("Schedule cleared for %s", day)
        else:
            _LOGGER.error("Invalid day: %s", day)

    def copy_schedule(self, from_day: str, to_day: str) -> None:
        """Copy schedule from one day to another."""
        if from_day not in DAYS_OF_WEEK or to_day not in DAYS_OF_WEEK:
            _LOGGER.error("Invalid day: %s or %s", from_day, to_day)
            return

        if from_day not in self.coordinator.schedule_data:
            _LOGGER.error("No schedule found for %s", from_day)
            return

        self.coordinator.schedule_data[to_day] = self.coordinator.schedule_data[from_day].copy()
        _LOGGER.info("Schedule copied from %s to %s", from_day, to_day)
