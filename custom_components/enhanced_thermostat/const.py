"""Constants for the Enhanced Thermostat integration."""
from typing import Final

DOMAIN: Final = "enhanced_thermostat"

# Config entry keys
CONF_SOURCE_ENTITY: Final = "source_entity"
CONF_SAFETY_MIN_TEMP: Final = "safety_min_temp"
CONF_SAFETY_MAX_TEMP: Final = "safety_max_temp"
CONF_SAFETY_ENABLED: Final = "safety_enabled"
CONF_HYSTERESIS: Final = "hysteresis"
CONF_SCHEDULE_ENABLED: Final = "schedule_enabled"
CONF_SCHEDULE_DATA: Final = "schedule_data"
CONF_TRACKING_ENABLED: Final = "tracking_enabled"

# Defaults
DEFAULT_SAFETY_MIN_TEMP: Final = 10.0
DEFAULT_SAFETY_MAX_TEMP: Final = 30.0
DEFAULT_HYSTERESIS: Final = 0.5
DEFAULT_SAFETY_ENABLED: Final = True
DEFAULT_SCHEDULE_ENABLED: Final = True
DEFAULT_TRACKING_ENABLED: Final = True

# Attributes
ATTR_SAFETY_ACTIVE: Final = "safety_active"
ATTR_SCHEDULE_ACTIVE: Final = "schedule_active"
ATTR_NEXT_SCHEDULE_EVENT: Final = "next_schedule_event"
ATTR_DAILY_HEATING_HOURS: Final = "daily_heating_hours"
ATTR_DAILY_COOLING_HOURS: Final = "daily_cooling_hours"
ATTR_OVERRIDE_UNTIL: Final = "override_until"

# Services
SERVICE_SET_SCHEDULE: Final = "set_schedule"
SERVICE_CLEAR_SCHEDULE: Final = "clear_schedule"
SERVICE_COPY_SCHEDULE: Final = "copy_schedule"
SERVICE_SET_OVERRIDE: Final = "set_override"
SERVICE_CLEAR_OVERRIDE: Final = "clear_override"
SERVICE_EXPORT_USAGE: Final = "export_usage"

# Days of week
DAYS_OF_WEEK: Final = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

# Update intervals
UPDATE_INTERVAL_SECONDS: Final = 30
TRACKING_INTERVAL_SECONDS: Final = 60

# Notification
NOTIFICATION_ID: Final = "enhanced_thermostat_safety"
NOTIFICATION_TITLE: Final = "Enhanced Thermostat Safety Alert"
