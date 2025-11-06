# P8 Pro Drone Controller V4 - Installation Guide

## System Requirements

### Hardware Requirements
- Computer with WiFi capability
- P8 Pro drone with WiFi connectivity
- Minimum 4GB RAM recommended
- 100MB free disk space

### Software Requirements
- Python 3.8 or higher
- Windows 10/11, macOS 10.14+, or Ubuntu 18.04+
- WiFi adapter with support for 2.4GHz networks

## Installation Steps

### 1. Install Python
If Python is not installed on your system:

**Windows:**
1. Download Python from [python.org](https://python.org)
2. Run the installer and check "Add Python to PATH"
3. Verify installation: `python --version`

**macOS:**
```bash
# Using Homebrew
brew install python

# Or download from python.org
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### 2. Download the Software
1. Download or clone the P8 Pro Drone Controller V4 files
2. Extract to a folder like `C:\DroneController` or `~/DroneController`

### 3. Install Dependencies
Open a terminal/command prompt in the software folder and run:

```bash
pip install -r requirements.txt
```

Required packages:
- `tkinter` (usually included with Python)
- `pygame` (for joystick support)
- `PyYAML` (for configuration files)
- `numpy` (for numerical calculations)
- `Pillow` (for image processing)
- `pyserial` (for serial communication)

### 4. Configure the Software
1. Edit `config/drone_config.yaml` if needed
2. Set your drone's IP address (default: 192.168.1.1)
3. Adjust other settings as required

### 5. Test Installation
Run the software to test installation:

```bash
python main.py
```

## P8 Pro Drone Setup

### 1. Drone Preparation
1. Ensure drone battery is fully charged
2. Power on the drone
3. Wait for the drone's WiFi network to appear

### 2. Network Connection
1. Connect your computer to the drone's WiFi network
   - Network name usually: `P8PRO_XXXXXX`
   - Password: Check drone manual or sticker
2. Verify connection by pinging: `ping 192.168.1.1`

### 3. First Connection Test
1. Launch the software: `python main.py`
2. Click "Connect" in the application
3. If successful, you should see "Connected" status
4. Check that telemetry data appears

## Troubleshooting

### Common Issues

**"Failed to connect to drone"**
- Check WiFi connection to drone
- Verify drone IP address (default: 192.168.1.1)
- Ensure drone is powered on and in WiFi mode
- Try restarting both drone and software

**"Module not found" errors**
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version`
- Try using `python3` instead of `python`

**GUI doesn't appear**
- Check if tkinter is installed: `python -c "import tkinter"`
- On Linux, install tkinter: `sudo apt install python3-tk`
- Update graphics drivers

**Connection drops frequently**
- Move closer to drone (within 30 meters)
- Check for WiFi interference
- Ensure drone battery is sufficient
- Try changing WiFi channel in drone settings

**Controls not responding**
- Check that drone is in "SDK mode"
- Verify takeoff was successful
- Check battery level (must be >20%)
- Try emergency stop and reconnect

### Performance Issues

**Slow response times**
- Reduce GUI update frequency in config
- Close other network-intensive applications
- Check computer CPU usage

**High CPU usage**
- Disable debug logging
- Reduce telemetry update rate
- Close unnecessary applications

## Configuration

### Network Settings
Edit `config/drone_config.yaml`:

```yaml
network:
  drone_ip: "192.168.1.1"     # Your drone's IP
  command_port: 8889          # Command port
  state_port: 8890            # Telemetry port
  connection_timeout: 5.0     # Connection timeout
```

### Flight Parameters
```yaml
flight:
  max_altitude: 500           # Maximum height (cm)
  max_speed: 100             # Maximum speed (10-100)
  default_speed: 50          # Default speed
  min_battery_level: 20      # Minimum battery for flight
```

### Safety Settings
```yaml
safety:
  emergency_landing_enabled: true
  auto_land_low_battery: true
  auto_land_battery_threshold: 10
  max_flight_time: 1200      # 20 minutes
```

## Advanced Configuration

### Logging
Logs are saved to the `logs/` directory:
- `drone_controller.log` - General application logs
- `errors.log` - Error messages only

### Custom Key Bindings
Default keyboard controls:
- `W` - Forward
- `S` - Backward  
- `A` - Left
- `D` - Right
- `Q` - Rotate left
- `E` - Rotate right
- `R` - Up
- `F` - Down
- `T` - Takeoff
- `L` - Land
- `Space` - Emergency stop

### Network Troubleshooting

**Find Drone IP Address:**
```bash
# Windows
arp -a | findstr "192.168.1"

# macOS/Linux
arp -a | grep "192.168.1"
```

**Test Connection:**
```bash
# Ping drone
ping 192.168.1.1

# Test specific port
telnet 192.168.1.1 8889
```

## Support

### Log Files
When reporting issues, include:
- `logs/drone_controller.log`
- `logs/errors.log`
- Your configuration file
- System information (OS, Python version)

### Common Solutions
1. **Restart everything**: Drone, software, computer WiFi
2. **Check permissions**: Some systems require admin rights
3. **Firewall**: Ensure ports 8889-8890 are not blocked
4. **Antivirus**: Add software folder to exclusions

### Getting Help
1. Check this documentation
2. Review log files for error messages
3. Try default configuration settings
4. Test with a simple ping to the drone

## Next Steps
Once installed and working:
1. Read the User Manual (`docs/user_manual.md`)
2. Practice in a safe, open area
3. Familiarize yourself with emergency procedures
4. Customize settings for your preferences