# Enhanced Z-Wave Thermostat for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/BKDude/enhanced-zwave-thermostat-v3.svg)](https://github.com/BKDude/enhanced-zwave-thermostat-v3/releases)
[![License](https://img.shields.io/github/license/BKDude/enhanced-zwave-thermostat-v3.svg)](LICENSE)

A powerful Home Assistant HACS integration that adds Nest-like features to any Z-Wave or Wi-Fi thermostat, including safety temperature monitoring, advanced scheduling, and usage tracking.

## 🎯 Background

Google discontinued support for Gen 1 and Gen 2 Nest thermostats, removing remote control functionality. This integration brings those beloved features back to your Z-Wave thermostats like the Honeywell T6, Ecobee, and others through Home Assistant.

## ✨ Features

### 🔥 Safety Temperature Protection
- **Automatic Safety Override**: Prevents dangerous temperatures when thermostat is off
- **Configurable Min/Max Thresholds**: Set your safe temperature range (default: 10°C - 30°C)
- **Smart Hysteresis**: Prevents rapid cycling with configurable buffer (default: 0.5°C)
- **Instant Notifications**: Get alerted via Home Assistant when safety mode activates
- **Auto-Recovery**: Automatically returns thermostat to OFF when temperature normalizes

**How it works**: If your thermostat is OFF and temperature drops below the minimum safety threshold, the integration automatically switches to HEAT mode. Once temperature rises above the threshold (plus hysteresis), it returns to OFF.

### 📅 Advanced Scheduling
- **7-Day Weekly Schedule**: Different schedules for each day of the week
- **Multiple Time Blocks**: Set as many temperature changes per day as needed
- **Copy/Paste Schedules**: Easily duplicate schedules between days
- **Manual Override**: Any manual change holds until the next scheduled event
- **Flexible Configuration**: Configure via services (UI panel coming soon)

**Example Schedule**:
```yaml
Monday: 6:00 → 20°C (Heat), 8:30 → OFF, 17:30 → 21°C (Heat)
Tuesday: Copy from Monday
Sunday: 7:00 → 18°C (Heat), 22:00 → 15°C (Heat)
```

### 📊 Usage Tracking & Reporting
- **Real-Time Tracking**: Monitor daily heating and cooling runtime
- **Historical Data**: Stores up to 90 days of usage history
- **CSV Export**: Export usage data for external analysis
- **Sensor Entities**: Separate sensors for heating and cooling hours
- **Daily Reset**: Counters automatically reset at midnight

### 🎛️ Climate Entity Proxy
- **Seamless Integration**: Acts as a drop-in replacement for your existing thermostat
- **Full Feature Support**: All original thermostat features work through the proxy
- **Enhanced Attributes**: Additional attributes show safety status, schedule info, and override state
- **No Data Loss**: Original thermostat entity remains unchanged and accessible

## 🚀 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/BKDude/enhanced-zwave-thermostat-v3`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Enhanced Z-Wave Thermostat"
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the `enhanced_thermostat` folder
3. Copy to `custom_components/` directory in your Home Assistant config folder
4. Restart Home Assistant

## ⚙️ Configuration

### Setup via UI

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **Enhanced Z-Wave Thermostat**
4. Follow the setup wizard:

#### Step 1: Select Thermostat
- **Source Climate Entity**: Choose your existing thermostat entity
- **Friendly Name**: (Optional) Custom name for the enhanced thermostat

#### Step 2: Safety Settings
- **Enable Safety Temperature**: Toggle safety monitoring on/off
- **Minimum Safety Temperature**: Temperature below which heating activates (°C)
- **Maximum Safety Temperature**: Temperature above which cooling activates (°C)
- **Hysteresis**: Temperature buffer to prevent rapid cycling (°C)

#### Step 3: Features
- **Enable Scheduling**: Turn on/off the scheduling engine
- **Enable Usage Tracking**: Turn on/off runtime tracking and sensors

### Example Configuration

**Safety Settings**:
- Minimum: 10°C (prevents freezing)
- Maximum: 30°C (prevents overheating)
- Hysteresis: 0.5°C

This means:
- If OFF and temp drops to 9.9°C → Switch to HEAT mode targeting 10.5°C
- When temp reaches 10.5°C → Return to OFF
- If OFF and temp rises to 30.1°C → Switch to COOL mode targeting 29.5°C
- When temp reaches 29.5°C → Return to OFF

## 📋 Services

### Set Schedule

Set the schedule for a specific day:

```yaml
service: enhanced_thermostat.set_schedule
target:
  entity_id: climate.enhanced_thermostat
data:
  day: monday
  events:
    - time: "06:00"
      mode: heat
      temperature: 20
    - time: "08:30"
      mode: "off"
    - time: "17:30"
      mode: heat
      temperature: 21
    - time: "22:00"
      mode: heat
      temperature: 18
```

### Clear Schedule

Clear schedule for one day or all days:

```yaml
# Clear specific day
service: enhanced_thermostat.clear_schedule
target:
  entity_id: climate.enhanced_thermostat
data:
  day: monday

# Clear all days
service: enhanced_thermostat.clear_schedule
target:
  entity_id: climate.enhanced_thermostat
```

### Copy Schedule

Copy schedule from one day to another:

```yaml
service: enhanced_thermostat.copy_schedule
target:
  entity_id: climate.enhanced_thermostat
data:
  from_day: monday
  to_day: tuesday
```

### Set Override

Set manual override until a specific time:

```yaml
service: enhanced_thermostat.set_override
target:
  entity_id: climate.enhanced_thermostat
data:
  until: "2025-10-01T18:00:00"
```

### Clear Override

Clear current override:

```yaml
service: enhanced_thermostat.clear_override
target:
  entity_id: climate.enhanced_thermostat
```

### Export Usage

Export usage data as CSV:

```yaml
service: enhanced_thermostat.export_usage
target:
  entity_id: climate.enhanced_thermostat
data:
  days: 30  # Export last 30 days
```

## 🎨 Lovelace UI Examples

### Basic Thermostat Card

```yaml
type: thermostat
entity: climate.enhanced_thermostat
```

### Enhanced Card with Attributes

```yaml
type: entities
entities:
  - entity: climate.enhanced_thermostat
  - type: attribute
    entity: climate.enhanced_thermostat
    attribute: safety_active
    name: Safety Mode Active
  - type: attribute
    entity: climate.enhanced_thermostat
    attribute: next_schedule_event
    name: Next Schedule Event
  - entity: sensor.enhanced_thermostat_daily_heating_hours
    name: Today's Heating
  - entity: sensor.enhanced_thermostat_daily_cooling_hours
    name: Today's Cooling
```

### Custom Button Card for Schedule

```yaml
type: custom:button-card
entity: climate.enhanced_thermostat
name: Copy Monday Schedule
tap_action:
  action: call-service
  service: enhanced_thermostat.copy_schedule
  service_data:
    from_day: monday
    to_day: tuesday
```

## 📈 Usage Tracking

The integration creates two sensor entities:

- `sensor.enhanced_thermostat_daily_heating_hours`: Daily heating runtime
- `sensor.enhanced_thermostat_daily_cooling_hours`: Daily cooling runtime

Both sensors:
- Reset at midnight
- Store historical data for 90 days
- Can be used in graphs and statistics
- Support CSV export for external analysis

### Example Usage Graph

```yaml
type: history-graph
entities:
  - sensor.enhanced_thermostat_daily_heating_hours
  - sensor.enhanced_thermostat_daily_cooling_hours
hours_to_show: 168  # 7 days
```

## 🔧 Troubleshooting

### Safety Mode Not Activating

1. Verify safety temperature is enabled in configuration
2. Check that thermostat is in OFF mode
3. Confirm current temperature is outside safety range
4. Check Home Assistant logs for errors

### Schedule Not Executing

1. Verify scheduling is enabled in configuration
2. Check that schedule is properly set for the day
3. Verify no manual override is active
4. Check `next_schedule_event` attribute for next execution

### Usage Sensors Not Updating

1. Verify tracking is enabled in configuration
2. Check that thermostat reports `hvac_action` attribute
3. Confirm coordinator is updating (check last_updated attribute)

### Integration Not Loading

1. Check Home Assistant logs for errors
2. Verify source climate entity exists and is accessible
3. Ensure custom_components folder has correct permissions
4. Try removing and re-adding the integration

## 🆚 Comparison with Other Integrations

| Feature                  | Generic Thermostat | Better Thermostat | Awesome Thermostat | Enhanced Thermostat |
|--------------------------|--------------------|--------------------|---------------------|---------------------|
| Scheduling               | ❌                 | ❌                 | ❌                  | ✅                  |
| Safety Temperature       | ❌                 | ❌                 | ❌                  | ✅                  |
| Usage Reporting          | ❌                 | ❌                 | ❌                  | ✅                  |
| Window/Door Detection    | ❌                 | ✅                 | ✅                  | ❌ (planned)        |
| Presence Automation      | ❌                 | ❌                 | ✅                  | ❌ (planned)        |
| External Sensor Support  | ❌                 | ✅                 | ❌                  | ❌                  |
| Easy Setup via UI        | ❌                 | ✅                 | ❌                  | ✅                  |

## 🗺️ Roadmap

### Version 1.1 (Planned)
- [ ] Custom Lovelace panel for schedule editing
- [ ] Graphical schedule timeline view
- [ ] Quick schedule templates (weekday/weekend)

### Version 1.2 (Planned)
- [ ] Window/door sensor integration
- [ ] Presence detection automation
- [ ] Away mode with reduced temperatures

### Version 2.0 (Future)
- [ ] Multi-thermostat grouping
- [ ] Advanced analytics and reporting
- [ ] Machine learning for optimal scheduling
- [ ] Integration with energy monitoring

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the Google Nest thermostat interface
- Built for the Home Assistant community
- Thanks to all contributors and testers

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/BKDude/enhanced-zwave-thermostat-v3/issues)
- **Discussions**: [GitHub Discussions](https://github.com/BKDude/enhanced-zwave-thermostat-v3/discussions)
- **Community**: [Home Assistant Forum](https://community.home-assistant.io/)

## ⭐ Star History

If you find this integration useful, please consider starring the repository!

---

**Made with ❤️ for the Home Assistant community**
