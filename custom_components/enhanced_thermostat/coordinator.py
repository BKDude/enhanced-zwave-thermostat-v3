"""Coordinator for Enhanced Thermostat integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    UPDATE_INTERVAL_SECONDS,
    CONF_SOURCE_ENTITY,
)

_LOGGER = logging.getLogger(__name__)


class EnhancedThermostatCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Enhanced Thermostat data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.config_entry = entry
        self._source_entity_id = entry.data.get(CONF_SOURCE_ENTITY, "")
        self._schedule_data: dict[str, list[dict[str, Any]]] = {}
        self._override_until: str | None = None
        self._safety_triggered: bool = False

    @property
    def source_entity_id(self) -> str:
        """Return the source entity ID."""
        return self._source_entity_id

    @source_entity_id.setter
    def source_entity_id(self, value: str) -> None:
        """Set the source entity ID."""
        self._source_entity_id = value

    @property
    def schedule_data(self) -> dict[str, list[dict[str, Any]]]:
        """Return the schedule data."""
        return self._schedule_data

    @schedule_data.setter
    def schedule_data(self, value: dict[str, list[dict[str, Any]]]) -> None:
        """Set the schedule data."""
        self._schedule_data = value

    @property
    def override_until(self) -> str | None:
        """Return the override timestamp."""
        return self._override_until

    @override_until.setter
    def override_until(self, value: str | None) -> None:
        """Set the override timestamp."""
        self._override_until = value

    @property
    def safety_triggered(self) -> bool:
        """Return if safety mode is triggered."""
        return self._safety_triggered

    @safety_triggered.setter
    def safety_triggered(self, value: bool) -> None:
        """Set safety triggered state."""
        self._safety_triggered = value

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from source entity."""
        try:
            if not self._source_entity_id:
                raise UpdateFailed("Source entity not configured")
                
            source_state = self.hass.states.get(self._source_entity_id)
            
            if source_state is None:
                raise UpdateFailed(f"Source entity {self._source_entity_id} not found")

            return {
                "state": source_state.state,
                "attributes": dict(source_state.attributes),
                "last_updated": source_state.last_updated,
            }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with source entity: {err}") from err

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value from entry data or options."""
        if key in self.config_entry.options:
            return self.config_entry.options[key]
        return self.config_entry.data.get(key, default)
