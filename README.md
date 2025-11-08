# P8 Pro Drone Controller V4

A comprehensive Python application for controlling P8 Pro drones via WiFi connection.

## Features

- **WiFi Communication**: Connect to P8 Pro drone through WiFi network
- **Flight Control**: Complete flight control including takeoff, landing, movement, and rotation
- **Real-time Telemetry**: Monitor drone status, battery, altitude, and GPS coordinates
- **Safety Features**: Emergency stop, connection monitoring, and automatic failsafe
- **User-friendly GUI**: Intuitive graphical interface for easy drone control
- **Configuration Management**: Customizable settings for different drone models and preferences

## Requirements

- Python 3.8 or higher
- P8 Pro drone with WiFi capability
- Windows/Linux/macOS computer with WiFi

## Installation

1. Clone or download this repository
2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your drone settings in `config/drone_config.yaml`
4. Run the application:
   ```bash
   python main.py
   ```

## Quick Start

1. Power on your P8 Pro drone
2. Connect your computer to the drone's WiFi network
3. Launch the application
4. Click "Connect" to establish communication
5. Use the control interface to fly your drone

## Safety Notice

- Always maintain visual line of sight with your drone
- Ensure adequate battery level before flight
- Be aware of local drone regulations and restrictions
- Use emergency stop if needed
- Practice in open areas away from people and property

## Configuration

Edit `config/drone_config.yaml` to customize:
- Network settings (IP address, port)
- Flight parameters (speed, altitude limits)
- Safety settings (battery thresholds, timeouts)
- GUI preferences

## Support

For issues and questions, please refer to the documentation in the `docs/` folder.

## License

This software is provided as-is for educational and personal use.