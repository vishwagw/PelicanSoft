# P8 Pro Drone Controller V4 - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Interface](#user-interface)
3. [Flight Operations](#flight-operations)
4. [Safety Features](#safety-features)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Getting Started

### Pre-Flight Checklist
Before each flight, verify:
- [ ] Drone battery is fully charged (>80%)
- [ ] Computer battery is sufficient for flight duration
- [ ] Clear flight area (minimum 10m radius)
- [ ] No people, vehicles, or obstacles nearby
- [ ] Weather conditions are suitable (no strong wind/rain)
- [ ] Local regulations allow drone flight
- [ ] Software is running and connected

### First Flight
1. **Connect to Drone**
   - Power on P8 Pro drone
   - Connect computer to drone's WiFi network
   - Launch software: `python main.py`
   - Click "Connect" button
   - Wait for "Connected" status

2. **Initialize System**
   - Check battery level (should show in status panel)
   - Verify telemetry data is updating
   - Test connection with small movements

3. **Start Video Streaming (Optional but Recommended)**
   - Click "Start Video" button for one-click video streaming with HUD
   - This automatically opens camera window and starts video feed
   - HUD overlay shows flight data, artificial horizon, and compass
   - Alternative: Click "Open Camera" then manually start video in video window

4. **Takeoff**
   - Click "Takeoff" button or press `T`
   - Drone will automatically rise to ~1 meter
   - Wait for stable hover before proceeding

## User Interface

### Main Window Layout

```
┌─────────────────────────────────────────────────────┐
│ Connection Panel                                    │
│ [IP: 192.168.1.1] [Port: 8889] [Connect] [Status]  │
├─────────────────┬───────────────────────────────────┤
│ Drone Status    │ Flight Controls                   │
│ Battery: 85%    │ [Takeoff] [Land]                  │
│ Altitude: 120cm │                                   │
│ Speed: 30cm/s   │     ↑                             │
│ Mode: Manual    │   ←   → ↺ ↻                       │
│ Flying: Yes     │     ↓                             │
│ [EMERGENCY]     │ [Up] [Down]                       │
│                 │ Speed: |||||||||| 50              │
├─────────────────┴───────────────────────────────────┤
│ Telemetry Display                                   │
│ [16:23:45] bat:85 h:120 vgx:0 vgy:5 vgz:0 ...      │
├─────────────────────────────────────────────────────┤
│ Log Messages                                        │
│ [16:23:45] Connected to drone                       │
│ [16:23:47] Takeoff successful                       │
└─────────────────────────────────────────────────────┘
```

### Control Elements

**Connection Panel:**
- **IP Address**: Drone's network address
- **Port**: Communication port (usually 8889)
- **Connect/Disconnect**: Establish/terminate connection
- **Status**: Shows connection state

**Status Panel:**
- **Battery**: Current battery percentage
- **Altitude**: Height above takeoff point (cm)
- **Speed**: Current movement speed
- **Mode**: Flight mode (Manual/Auto/Takeoff/Land)
- **Flying**: Whether drone is airborne
- **Emergency**: Emergency stop button

**Control Panel:**
- **Takeoff/Land**: Basic flight operations
- **Directional Controls**: Move drone in 4 directions
- **Rotation**: Turn left/right
- **Vertical**: Move up/down
- **Speed Slider**: Adjust movement speed

### Keyboard Controls
Enable in settings for hands-free operation:

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| `W` | Forward | `R` | Up |
| `S` | Backward | `F` | Down |
| `A` | Left | `Q` | Rotate Left |
| `D` | Right | `E` | Rotate Right |
| `T` | Takeoff | `L` | Land |
| `Space` | Emergency Stop | | |

## Flight Operations

### Basic Flight Sequence

1. **Pre-Flight**
   ```
   Connect → Check Status → Initialize
   ```

2. **Takeoff**
   ```
   Press Takeoff → Wait for Hover → Check Stability
   ```

3. **Flight**
   ```
   Use Controls → Monitor Status → Watch Battery
   ```

4. **Landing**
   ```
   Return to Start → Press Land → Wait for Complete Stop
   ```

### Movement Commands

**Linear Movement:**
- Default distance: 30cm per command
- Range: 20-500cm (configurable)
- Speed affects duration, not distance

**Rotation:**
- Default: 45° per command
- Range: 1-360°
- Clockwise (CW) or Counter-clockwise (CCW)

**Altitude:**
- Takeoff height: ~100cm
- Maximum: 500cm (configurable)
- Minimum: Ground level

### Flight Modes

**Manual Mode:**
- Direct control via buttons/keyboard
- Immediate response to commands
- Pilot responsible for all decisions

**Auto Mode** (Future feature):
- Autonomous flight patterns
- Pre-programmed routes
- Automatic obstacle avoidance

## Safety Features

### Automatic Safety Systems

**Battery Protection:**
- Warning at 20% battery
- Automatic landing at 10% battery
- Emergency stop at 5% battery

**Flight Time Limits:**
- Maximum flight time: 20 minutes
- Warning at 16 minutes (80%)
- Forced landing at limit

**Connection Monitoring:**
- Heartbeat every 5 seconds
- Auto-land on connection loss
- Reconnection attempts

**Altitude Limits:**
- Maximum height enforcement
- Warning when approaching limits
- Automatic descent if exceeded

### Manual Safety Controls

**Emergency Stop:**
- Immediately cuts all motors
- Use only in emergency situations
- May cause crash landing
- Press red button or Spacebar

**Emergency Landing:**
- Controlled descent to ground
- Maintains stability during descent
- Safer than emergency stop
- Triggered automatically or manually

### Safety Alerts

**Warning Levels:**
- **INFO**: Normal operations
- **WARNING**: Attention required
- **CRITICAL**: Immediate action needed
- **EMERGENCY**: Danger - automated response

**Common Alerts:**
```
LOW BATTERY: 15% - Consider landing soon
CRITICAL BATTERY: 8% - Landing automatically
HIGH ALTITUDE: 450cm - Approaching limit
CONNECTION LOST - Attempting emergency land
FLIGHT TIME WARNING: 17 minutes elapsed
```

## Advanced Features

### Telemetry Monitoring

**Real-time Data:**
- Battery percentage and voltage
- Altitude and barometric pressure
- Speed (X, Y, Z components)
- Attitude (pitch, roll, yaw)
- Temperature sensors
- Time of flight sensor

**Data Format:**
```
bat:85 h:120 vgx:0 vgy:5 vgz:0 pitch:2 roll:-1 yaw:45 temp:32 tof:115
```

### Configuration Options

**Network Settings:**
```yaml
network:
  drone_ip: "192.168.1.1"
  command_port: 8889
  state_port: 8890
```

**Flight Parameters:**
```yaml
flight:
  max_altitude: 500
  max_speed: 100
  default_speed: 50
  default_move_distance: 30
```

**Safety Settings:**
```yaml
safety:
  auto_land_battery_threshold: 10
  max_flight_time: 1200
  connection_timeout_action: "land"
```

### Logging System

**Log Files:**
- `logs/drone_controller.log` - All operations
- `logs/errors.log` - Errors only
- Automatic rotation when files get large
- Timestamped entries for debugging

**Log Levels:**
- **DEBUG**: Detailed operation info
- **INFO**: General operations
- **WARNING**: Potential issues
- **ERROR**: Operation failures

## Troubleshooting

### Connection Issues

**Problem: Cannot connect to drone**
```
Symptoms: "Failed to connect" message
Solutions:
1. Check WiFi connection to drone
2. Verify drone IP address
3. Restart drone and software
4. Check firewall settings
5. Try different USB port (if using adapter)
```

**Problem: Connection drops frequently**
```
Symptoms: Intermittent disconnection
Solutions:
1. Move closer to drone (<30m)
2. Check for WiFi interference
3. Ensure sufficient battery (both drone/computer)
4. Reduce other network activity
```

### Flight Control Issues

**Problem: Controls not responding**
```
Symptoms: Commands ignored or delayed
Solutions:
1. Check connection status
2. Verify drone is in SDK mode
3. Ensure successful takeoff
4. Check battery level (>20%)
5. Try emergency stop and reconnect
```

**Problem: Erratic flight behavior**
```
Symptoms: Unexpected movements
Solutions:
1. Check for strong winds
2. Verify flat takeoff surface
3. Recalibrate drone sensors
4. Reduce control sensitivity
```

### Software Issues

**Problem: GUI freezes or crashes**
```
Symptoms: Unresponsive interface
Solutions:
1. Close and restart software
2. Check system resources (RAM/CPU)
3. Update Python and dependencies
4. Check log files for errors
```

**Problem: High CPU/memory usage**
```
Symptoms: Slow performance
Solutions:
1. Reduce GUI update frequency
2. Lower telemetry update rate
3. Close other applications
4. Disable debug logging
```

## Best Practices

### Flight Safety

**Before Every Flight:**
1. Visual inspection of drone
2. Check propellers for damage
3. Verify battery charge levels
4. Test emergency stop function
5. Plan flight route and duration

**During Flight:**
1. Maintain visual line of sight
2. Monitor battery constantly
3. Be ready for emergency stop
4. Avoid crowded areas
5. Respect privacy and property

**After Flight:**
1. Land in open area
2. Power down in correct sequence
3. Check for any damage
4. Review flight logs if needed
5. Charge batteries for next flight

### Operational Guidelines

**Environmental Considerations:**
- Wind speed <15 mph (24 km/h)
- No precipitation
- Good visibility conditions
- Temperature within operating range
- Avoid magnetic interference areas

**Legal Compliance:**
- Check local drone regulations
- Respect no-fly zones
- Maintain required altitudes
- Register drone if required
- Obtain permits if necessary

**Battery Management:**
- Charge before each session
- Don't over-discharge
- Store at proper voltage
- Replace when degraded
- Keep spares available

### Performance Optimization

**For Best Performance:**
1. Use dedicated computer for control
2. Close unnecessary applications
3. Ensure strong WiFi signal
4. Keep software updated
5. Regular maintenance checks

**Customization Tips:**
1. Adjust control sensitivity to preference
2. Set comfortable keyboard shortcuts
3. Configure appropriate safety thresholds
4. Customize GUI layout if possible
5. Create flight profiles for different scenarios

## Emergency Procedures

### Emergency Situations

**Lost Connection:**
1. Stay calm and wait for auto-land
2. Try to reconnect software
3. Move closer to drone location
4. Be prepared for manual recovery

**Low Battery Emergency:**
1. Land immediately in nearest safe area
2. Don't attempt to return if far away
3. Mark landing location
4. Retrieve drone after landing

**Flyaway/Loss of Control:**
1. Press emergency stop immediately
2. Note last known position and direction
3. Check for signal interference
4. Begin search pattern if safe

**Crash/Hard Landing:**
1. Approach carefully (props may still spin)
2. Disconnect battery immediately
3. Check for damage before handling
4. Document incident for insurance

### Recovery Procedures

**After Emergency Landing:**
1. Ensure drone is completely powered down
2. Visual inspection for damage
3. Check all connections and sensors
4. Test basic functions before next flight
5. Review logs to understand cause

**Data Recovery:**
1. Check telemetry logs for flight data
2. Export important data before restart
3. Save configuration if customized
4. Backup flight recordings if available

Remember: Safety is the top priority. When in doubt, land the drone and assess the situation on the ground.