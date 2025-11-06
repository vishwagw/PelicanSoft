# P8 Pro Drone Controller V4 - API Reference

## Overview
This document provides technical reference for the P8 Pro Drone Controller V4 software architecture, classes, and methods.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   main.py                           │
│              Application Entry Point                │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                GUI Layer                            │
│           (src/gui/main_window.py)                  │
├─────────────────┬───────────────────────────────────┤
│    Control      │    Communication   │   Utilities  │
│    Layer        │       Layer        │    Layer     │
│                 │                    │              │
│ DroneController │  DroneConnection   │SafetyManager │
│                 │                    │TelemetryParser│
│                 │                    │   Logger     │
└─────────────────┴────────────────────┴──────────────┘
```

## Core Classes

### DroneConnection
**File:** `src/communication/wifi_connection.py`

Manages WiFi communication with the P8 Pro drone.

#### Constructor
```python
DroneConnection(drone_ip="192.168.1.1", command_port=8889, 
                state_port=8890, video_port=11111)
```

**Parameters:**
- `drone_ip` (str): IP address of the drone
- `command_port` (int): Port for sending commands (default: 8889)
- `state_port` (int): Port for receiving telemetry (default: 8890)
- `video_port` (int): Port for video stream (default: 11111)

#### Methods

##### connect() → bool
Establishes connection to the drone.

**Returns:** `True` if connection successful, `False` otherwise

**Example:**
```python
connection = DroneConnection("192.168.1.1")
if connection.connect():
    print("Connected to drone")
```

##### disconnect() → None
Disconnects from drone and cleans up resources.

##### send_command(command: str, timeout: float = 2.0) → Optional[str]
Sends command to drone and waits for response.

**Parameters:**
- `command` (str): Command string to send
- `timeout` (float): Response timeout in seconds

**Returns:** Response string or `None` if timeout

**Example:**
```python
response = connection.send_command("battery?")
if response:
    battery_level = int(response)
```

##### send_command_async(command: str) → None
Sends command asynchronously without waiting for response.

##### set_telemetry_callback(callback: Callable[[str], None]) → None
Sets callback function for telemetry data.

**Example:**
```python
def on_telemetry(data):
    print(f"Telemetry: {data}")

connection.set_telemetry_callback(on_telemetry)
```

#### Properties
- `is_connected` (bool): Connection status
- `drone_ip` (str): Current drone IP address
- `command_port` (int): Command port number
- `state_port` (int): Telemetry port number

---

### DroneController
**File:** `src/control/drone_controller.py`

High-level drone control interface.

#### Constructor
```python
DroneController(connection: DroneConnection)
```

**Parameters:**
- `connection`: DroneConnection instance

#### Methods

##### initialize() → bool
Initializes drone for control.

**Returns:** `True` if initialization successful

##### takeoff() → bool
Performs automatic takeoff.

**Returns:** `True` if takeoff successful

**Example:**
```python
if controller.takeoff():
    print("Takeoff successful")
    time.sleep(3)  # Wait for stabilization
```

##### land() → bool
Performs automatic landing.

**Returns:** `True` if landing successful

##### emergency_stop() → bool
Emergency stop - immediate motor shutdown.

**Returns:** `True` if emergency stop successful

**Warning:** This will cause the drone to fall. Use only in emergencies.

##### move_forward(distance: int) → bool
Move forward by specified distance.

**Parameters:**
- `distance` (int): Distance in cm (20-500)

**Returns:** `True` if movement successful

##### move_backward(distance: int) → bool
Move backward by specified distance.

##### move_left(distance: int) → bool
Move left by specified distance.

##### move_right(distance: int) → bool
Move right by specified distance.

##### move_up(distance: int) → bool
Move up by specified distance.

##### move_down(distance: int) → bool
Move down by specified distance.

##### rotate_clockwise(degrees: int) → bool
Rotate clockwise by specified degrees.

**Parameters:**
- `degrees` (int): Rotation in degrees (1-360)

##### rotate_counterclockwise(degrees: int) → bool
Rotate counterclockwise by specified degrees.

##### set_speed(speed: int) → bool
Set movement speed.

**Parameters:**
- `speed` (int): Speed value (10-100)

##### get_battery_level() → Optional[int]
Get current battery level.

**Returns:** Battery percentage or `None` if unavailable

##### get_flight_status() → Dict[str, Any]
Get comprehensive flight status.

**Returns:** Dictionary with flight status information

**Example:**
```python
status = controller.get_flight_status()
print(f"Flying: {status['is_flying']}")
print(f"Battery: {status['battery']}%")
print(f"Altitude: {status['altitude']}cm")
```

#### Properties
- `is_flying` (bool): Whether drone is airborne
- `current_mode` (FlightMode): Current flight mode
- `current_battery` (int): Battery percentage
- `current_altitude` (int): Altitude in cm
- `current_speed` (int): Current speed setting

---

### TelemetryParser
**File:** `src/utils/telemetry_parser.py`

Parses drone telemetry data into structured format.

#### Methods

##### parse(telemetry_string: str) → Dict[str, Any]
Parse telemetry string into structured data.

**Parameters:**
- `telemetry_string` (str): Raw telemetry data from drone

**Returns:** Dictionary with parsed telemetry data

**Example:**
```python
parser = TelemetryParser()
data = parser.parse("bat:85 h:120 vgx:0 vgy:5 temp:32")
print(f"Battery: {data['battery']}%")
print(f"Altitude: {data['altitude']}cm")
```

##### format_for_display(parsed_data: Dict[str, Any]) → str
Format parsed data for human-readable display.

##### get_critical_alerts(parsed_data: Dict[str, Any]) → list
Check for critical conditions requiring attention.

**Returns:** List of alert messages

---

### SafetyManager
**File:** `src/utils/safety_manager.py`

Manages drone safety features and monitoring.

#### Constructor
```python
SafetyManager(controller: DroneController, config: Dict[str, Any])
```

#### Methods

##### start_monitoring() → None
Start safety monitoring.

##### stop_monitoring() → None
Stop safety monitoring.

##### trigger_emergency_stop(reason: str = "Emergency stop activated") → bool
Trigger emergency stop.

##### on_takeoff() → None
Called when drone takes off.

##### on_landing() → None
Called when drone lands.

##### on_telemetry_update(telemetry_data: Dict[str, Any]) → None
Called when telemetry data is received.

##### set_safety_alert_callback(callback: Callable) → None
Set callback for safety alerts.

##### get_safety_status() → Dict[str, Any]
Get current safety status.

---

### DroneControllerGUI
**File:** `src/gui/main_window.py`

Main application window for drone control.

#### Constructor
```python
DroneControllerGUI(config: dict)
```

#### Methods

##### run() → None
Start the GUI application.

##### connect_drone() → None
Connect to drone.

##### disconnect_drone() → None
Disconnect from drone.

##### takeoff_drone() → None
Initiate drone takeoff.

##### land_drone() → None
Initiate drone landing.

##### emergency_stop() → None
Execute emergency stop.

## Configuration System

### ConfigManager
**File:** `config/settings.py`

Manages application configuration.

#### Methods

##### load_config() → bool
Load configuration from file.

##### save_config() → bool
Save current configuration to file.

##### get(key_path: str, default=None) → Any
Get configuration value using dot notation.

**Example:**
```python
config = ConfigManager()
drone_ip = config.get('network.drone_ip', '192.168.1.1')
max_altitude = config.get('flight.max_altitude', 500)
```

##### set(key_path: str, value: Any) → bool
Set configuration value using dot notation.

##### get_section(section: str) → Dict[str, Any]
Get entire configuration section.

## Utility Functions

### Logging
**File:** `src/utils/logger.py`

##### setup_logging(log_level=logging.INFO, log_to_file=True) → None
Setup application logging.

##### DroneLogger(name: str)
Custom logger for drone operations.

**Methods:**
- `flight_event(event: str, **kwargs)` - Log flight-related events
- `command_sent(command: str, response: Optional[str] = None)` - Log commands
- `safety_alert(alert: str, level: str = "WARNING")` - Log safety alerts

## Error Handling

### Common Exceptions

#### ConnectionError
Raised when drone connection fails.

#### CommandTimeoutError
Raised when command times out.

#### SafetyException
Raised for safety-related issues.

#### ConfigurationError
Raised for configuration problems.

## Usage Examples

### Basic Flight Control
```python
from communication import DroneConnection
from control import DroneController

# Create connection
connection = DroneConnection("192.168.1.1")

# Connect to drone
if connection.connect():
    # Create controller
    controller = DroneController(connection)
    
    # Initialize
    if controller.initialize():
        # Takeoff
        if controller.takeoff():
            # Fly forward 100cm
            controller.move_forward(100)
            
            # Rotate 90 degrees
            controller.rotate_clockwise(90)
            
            # Land
            controller.land()
    
    # Disconnect
    connection.disconnect()
```

### Telemetry Monitoring
```python
from utils import TelemetryParser

parser = TelemetryParser()

def on_telemetry(data_string):
    parsed = parser.parse(data_string)
    
    # Check battery
    if 'battery' in parsed and parsed['battery'] < 20:
        print(f"Low battery warning: {parsed['battery']}%")
    
    # Check altitude
    if 'altitude' in parsed:
        print(f"Current altitude: {parsed['altitude']}cm")

connection.set_telemetry_callback(on_telemetry)
```

### Safety Monitoring
```python
from utils import SafetyManager

def on_safety_alert(event):
    level = event['level']
    message = event['message']
    print(f"SAFETY {level.value.upper()}: {message}")

safety = SafetyManager(controller, config)
safety.set_safety_alert_callback(on_safety_alert)
safety.start_monitoring()
```

## Constants and Enums

### FlightMode
```python
class FlightMode(Enum):
    MANUAL = "manual"
    AUTO = "auto"
    LAND = "land"
    TAKEOFF = "takeoff"
```

### SafetyLevel
```python
class SafetyLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"
```

## Threading Considerations

The software uses multiple threads:
- **Main Thread**: GUI and user interaction
- **Command Thread**: Command processing
- **Telemetry Thread**: Telemetry reception
- **Safety Thread**: Safety monitoring

**Thread Safety:**
- Use `threading.Lock` for shared resources
- GUI updates must use `root.after()` method
- Avoid blocking operations in main thread

## Performance Guidelines

### Optimization Tips
1. Limit telemetry update frequency
2. Use appropriate timeouts for commands
3. Implement connection pooling for multiple drones
4. Cache frequently accessed configuration values
5. Use background threads for I/O operations

### Memory Management
1. Clean up connections properly
2. Limit log file sizes
3. Clear old telemetry data periodically
4. Use weak references where appropriate

## Debugging

### Debug Mode
Enable debug logging in configuration:
```yaml
logging:
  level: "DEBUG"
advanced:
  enable_debug_mode: true
```

### Common Debug Commands
```python
# Check connection status
print(f"Connected: {connection.is_connected}")

# Get last command response
response = connection.get_latest_response()

# Check safety status
status = safety.get_safety_status()

# Validate configuration
errors = config.validate_config()
```

This API reference provides the foundation for extending and customizing the P8 Pro Drone Controller V4 software.