"""Enhanced Z-Wave Thermostat integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_SET_SCHEDULE,
    SERVICE_CLEAR_SCHEDULE,
    SERVICE_COPY_SCHEDULE,
    SERVICE_SET_OVERRIDE,
    SERVICE_CLEAR_OVERRIDE,
    SERVICE_EXPORT_USAGE,
)
from .coordinator import EnhancedThermostatCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Enhanced Thermostat component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Enhanced Thermostat from a config entry."""
    coordinator = EnhancedThermostatCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    await async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for the integration."""
    
    async def handle_set_schedule(call: ServiceCall) -> None:
        """Handle set_schedule service call."""
        entity_id = call.data.get("entity_id")
        day = call.data.get("day")
        events = call.data.get("events")
        
        # Find the coordinator for this entity
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if isinstance(coordinator, EnhancedThermostatCoordinator):
                # Get the climate entity's scheduler
                climate_entities = hass.states.async_entity_ids("climate")
                if entity_id in climate_entities:
                    from .scheduler import ThermostatScheduler
                    scheduler = ThermostatScheduler(coordinator)
                    scheduler.set_schedule(day, events)
                    break
    
    async def handle_clear_schedule(call: ServiceCall) -> None:
        """Handle clear_schedule service call."""
        entity_id = call.data.get("entity_id")
        day = call.data.get("day")
        
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if isinstance(coordinator, EnhancedThermostatCoordinator):
                climate_entities = hass.states.async_entity_ids("climate")
                if entity_id in climate_entities:
                    from .scheduler import ThermostatScheduler
                    scheduler = ThermostatScheduler(coordinator)
                    scheduler.clear_schedule(day)
                    break
    
    async def handle_copy_schedule(call: ServiceCall) -> None:
        """Handle copy_schedule service call."""
        entity_id = call.data.get("entity_id")
        from_day = call.data.get("from_day")
        to_day = call.data.get("to_day")
        
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if isinstance(coordinator, EnhancedThermostatCoordinator):
                climate_entities = hass.states.async_entity_ids("climate")
                if entity_id in climate_entities:
                    from .scheduler import ThermostatScheduler
                    scheduler = ThermostatScheduler(coordinator)
                    scheduler.copy_schedule(from_day, to_day)
                    break
    
    async def handle_set_override(call: ServiceCall) -> None:
        """Handle set_override service call."""
        entity_id = call.data.get("entity_id")
        until = call.data.get("until")
        
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if isinstance(coordinator, EnhancedThermostatCoordinator):
                climate_entities = hass.states.async_entity_ids("climate")
                if entity_id in climate_entities:
                    coordinator.override_until = until
                    break
    
    async def handle_clear_override(call: ServiceCall) -> None:
        """Handle clear_override service call."""
        entity_id = call.data.get("entity_id")
        
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if isinstance(coordinator, EnhancedThermostatCoordinator):
                climate_entities = hass.states.async_entity_ids("climate")
                if entity_id in climate_entities:
                    coordinator.override_until = None
                    break
    
    async def handle_export_usage(call: ServiceCall) -> None:
        """Handle export_usage service call."""
        entity_id = call.data.get("entity_id")
        days = call.data.get("days", 30)
        
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if isinstance(coordinator, EnhancedThermostatCoordinator):
                usage_tracker = getattr(coordinator, "usage_tracker", None)
                if usage_tracker:
                    csv_data = usage_tracker.export_csv()
                    _LOGGER.info("Usage data exported:\n%s", csv_data)
                    
                    # Create a persistent notification with the CSV data
                    from homeassistant.components.persistent_notification import async_create
                    async_create(
                        hass,
                        f"```\n{csv_data}\n```",
                        title="Enhanced Thermostat Usage Export",
                        notification_id="enhanced_thermostat_export",
                    )
                break
    
    # Register services
    if not hass.services.has_service(DOMAIN, SERVICE_SET_SCHEDULE):
        hass.services.async_register(DOMAIN, SERVICE_SET_SCHEDULE, handle_set_schedule)
    
    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_SCHEDULE):
        hass.services.async_register(DOMAIN, SERVICE_CLEAR_SCHEDULE, handle_clear_schedule)
    
    if not hass.services.has_service(DOMAIN, SERVICE_COPY_SCHEDULE):
        hass.services.async_register(DOMAIN, SERVICE_COPY_SCHEDULE, handle_copy_schedule)
    
    if not hass.services.has_service(DOMAIN, SERVICE_SET_OVERRIDE):
        hass.services.async_register(DOMAIN, SERVICE_SET_OVERRIDE, handle_set_override)
    
    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_OVERRIDE):
        hass.services.async_register(DOMAIN, SERVICE_CLEAR_OVERRIDE, handle_clear_override)
    
    if not hass.services.has_service(DOMAIN, SERVICE_EXPORT_USAGE):
        hass.services.async_register(DOMAIN, SERVICE_EXPORT_USAGE, handle_export_usage)
