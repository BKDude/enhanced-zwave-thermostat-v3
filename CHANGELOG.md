# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-01

### Added
- Initial release
- Climate entity proxy for Z-Wave and Wi-Fi thermostats
- Safety temperature monitoring with auto-override
- 7-day scheduling with multiple time blocks per day
- Manual override that holds until next scheduled event
- Usage tracking with daily heating/cooling sensors
- CSV export for usage data
- Copy/paste schedule between days
- UI-based configuration flow
- Options flow for runtime configuration changes
- Comprehensive service definitions
- Notification system for safety alerts
- Hysteresis support to prevent rapid cycling
- Full Home Assistant integration with HACS support

### Features
- **Safety Temperature**: Prevents dangerous conditions with automatic HVAC activation
- **Advanced Scheduling**: Nest-like 7-day schedule with flexible time blocks
- **Usage Reporting**: Track and export daily heating/cooling runtime
- **Manual Override**: Smart override system that respects scheduled events
- **Full Proxy**: Supports all original thermostat features transparently

## [Unreleased]

### Planned for 1.1.0
- Custom Lovelace panel for schedule editing
- Graphical schedule timeline view
- Quick schedule templates (weekday/weekend)
- Enhanced schedule validation

### Planned for 1.2.0
- Window/door sensor integration
- Presence detection automation
- Away mode with temperature reduction
- Advanced energy optimization

### Planned for 2.0.0
- Multi-thermostat grouping
- Machine learning for optimal scheduling
- Advanced analytics dashboard
- Integration with home energy monitoring
