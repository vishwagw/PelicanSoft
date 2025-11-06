# P8 Pro Drone Controller V4 - Video and HUD System Guide

## Overview
The P8 Pro Drone Controller V4 now includes comprehensive video streaming capabilities with an advanced HUD (Heads-Up Display) system for real-time flight data overlay.

## 🎥 Video Features

### Real-time Video Streaming
- **UDP-based streaming** from P8 Pro camera
- **720p/960p resolution** support
- **30 FPS target** frame rate
- **Automatic frame decoding** (JPEG/H.264)
- **Low-latency display** with frame buffering

### HUD Overlay System
- **Flight telemetry display** (battery, altitude, speed)
- **Artificial horizon** with pitch/roll indicators
- **Compass heading** display
- **Center crosshair** for targeting
- **Customizable colors** and elements
- **Warning indicators** for critical conditions

### Video Recording
- **MP4 format** recording with metadata
- **Telemetry synchronization** with video frames
- **Automatic filename generation** with timestamps
- **Background recording** without performance impact
- **Flight analysis** and reporting tools

## 🎮 Using the Video System

### Opening Video Window
1. **Launch the main application**:
   ```bash
   python main.py
   ```

2. **Click "Open Camera"** button in the connection panel

3. **The video window will open** with controls and display area

### Video Controls

#### Basic Controls
- **Start Video**: Begin video streaming from drone
- **Stop Video**: End video streaming
- **Start Recording**: Begin recording video with telemetry
- **Stop Recording**: End recording and save file
- **Snapshot**: Capture current frame as image
- **Toggle HUD**: Enable/disable HUD overlay

#### HUD Element Controls
- ☑️ **Crosshair**: Center targeting crosshair
- ☑️ **Telemetry**: Flight data display
- ☑️ **Horizon**: Artificial horizon indicator  
- ☑️ **Compass**: Heading display

### HUD Information Display

#### Top Left - Flight Data
```
BAT: 85%          # Battery percentage
ALT: 120cm        # Altitude above takeoff
SPD: 25.5cm/s     # Current speed
MODE: Manual      # Flight mode
```

#### Top Right - Sensors
```
TEMP: 32°C        # Internal temperature
TOF: 115cm        # Distance to ground
```

#### Bottom Right - Flight Time
```
TIME: 05:42       # Flight duration
```

#### Center - Navigation
```
    ↑             # Artificial horizon
←  +  →           # Center crosshair
    ↓
```

#### Top Center - Compass
```
   090°           # Current heading
```

## 🔧 Configuration

### Video Settings (`config/drone_config.yaml`)

```yaml
# Video and Camera Configuration
video:
  enable_video_stream: true        # Enable video streaming
  resolution_width: 960            # Video width (pixels)
  resolution_height: 720           # Video height (pixels)
  frame_rate: 30                   # Target frame rate (FPS)
  video_codec: "mp4v"              # Video codec for recording
  auto_start_stream: false         # Auto-start video when connecting
  recording_directory: "recordings" # Directory for video recordings

# HUD Configuration
hud:
  enable_hud: true                 # Enable HUD overlay
  show_crosshair: true             # Show center crosshair
  show_telemetry: true             # Show telemetry data
  show_artificial_horizon: true   # Show attitude indicator
  show_compass: true               # Show compass heading
  hud_color_r: 0                   # HUD color (Red component 0-255)
  hud_color_g: 255                 # HUD color (Green component 0-255)
  hud_color_b: 0                   # HUD color (Blue component 0-255)
  font_scale: 0.6                  # HUD font scale
  warning_color_r: 0               # Warning color (Red)
  warning_color_g: 0               # Warning color (Green)
  warning_color_b: 255             # Warning color (Blue)
```

### Network Configuration
```yaml
network:
  drone_ip: "192.168.1.1"          # Drone IP address
  video_port: 11111                # Video stream port
```

## 📹 Recording and Analysis

### Automatic Recording
- **Filename format**: `flight_recording_YYYYMMDD_HHMMSS.mp4`
- **Metadata file**: `flight_recording_YYYYMMDD_HHMMSS_metadata.json`
- **Storage location**: `recordings/` directory

### Recording Files Structure
```
recordings/
├── flight_recording_20241106_143022.mp4
├── flight_recording_20241106_143022_metadata.json
├── flight_recording_20241106_145230.mp4
└── flight_recording_20241106_145230_metadata.json
```

### Metadata Content
The metadata JSON file contains:
- **Recording information** (duration, resolution, frame count)
- **Synchronized telemetry data** with timestamps
- **Flight statistics** and events
- **Frame-by-frame correlation** data

### Post-Flight Analysis

#### Generate Flight Report
```python
from utils.video_recorder import create_flight_report

create_flight_report(
    "recordings/flight_recording_20241106_143022.mp4",
    "recordings/flight_recording_20241106_143022_metadata.json",
    "flight_report.html"
)
```

#### Export Telemetry Data
```python
from utils.video_recorder import TelemetryVideoAnalyzer

analyzer = TelemetryVideoAnalyzer(
    "recordings/flight_recording_20241106_143022.mp4",
    "recordings/flight_recording_20241106_143022_metadata.json"
)

# Export to CSV
analyzer.export_telemetry_csv("flight_data.csv")

# Get flight summary
summary = analyzer.get_flight_summary()
print(f"Max altitude: {summary['flight_stats']['altitude']['max']} cm")
print(f"Battery used: {summary['flight_stats']['battery']['start'] - summary['flight_stats']['battery']['end']}%")
```

## 🎯 HUD Customization

### Color Schemes

#### Default (Green)
```yaml
hud_color_r: 0
hud_color_g: 255
hud_color_b: 0
```

#### Blue Theme
```yaml
hud_color_r: 0
hud_color_g: 150
hud_color_b: 255
```

#### Military Green
```yaml
hud_color_r: 50
hud_color_g: 200
hud_color_b: 50
```

### Custom HUD Elements

#### Programmatic HUD Control
```python
from communication.video_stream import HUDOverlay

hud = HUDOverlay()

# Toggle specific elements
hud.toggle_element('crosshair')
hud.toggle_element('telemetry')
hud.toggle_element('horizon')
hud.toggle_element('compass')

# Change colors
hud.text_color = (255, 255, 0)  # Yellow
hud.warning_color = (255, 0, 255)  # Magenta
```

## 🚁 Camera Control Commands

### Video Stream Control
```python
# Start/stop video stream
controller.start_video_stream()
controller.stop_video_stream()

# Set video quality
controller.set_video_bitrate(3)  # 1-5 (low to high)
controller.set_video_resolution("high")  # "high" or "low"
controller.set_video_fps("middle")  # "low", "middle", "high"
```

### Camera Settings
- **Bitrate**: 1 (lowest) to 5 (highest quality)
- **Resolution**: "low" (480p) or "high" (720p)
- **Frame Rate**: "low" (15fps), "middle" (24fps), "high" (30fps)

## 🔍 Troubleshooting

### Video Stream Issues

#### "No Video Signal"
- Check drone WiFi connection
- Verify video port (11111) is not blocked
- Ensure drone camera is functioning
- Try restarting video stream

#### Poor Video Quality
```python
# Increase bitrate
controller.set_video_bitrate(5)

# Set high resolution
controller.set_video_resolution("high")

# Optimize frame rate
controller.set_video_fps("middle")
```

#### Recording Problems
- Check disk space in `recordings/` directory
- Verify write permissions
- Ensure OpenCV video codecs are installed
- Try different recording format

### Performance Optimization

#### High CPU Usage
```yaml
video:
  frame_rate: 20               # Reduce target FPS
hud:
  show_artificial_horizon: false  # Disable complex HUD elements
```

#### Network Optimization
- Move closer to drone (< 30 meters)
- Reduce other network activity
- Use 5GHz WiFi if available
- Check for interference

### Common Error Messages

#### "Failed to initialize video writer"
```bash
# Install additional codecs (Windows)
pip install opencv-python-headless

# Or try different codec
video_codec: "XVID"
```

#### "Frame decode error"
- Usually indicates network packet loss
- Move closer to drone
- Check WiFi signal strength
- Reduce video bitrate

## 🎬 Advanced Features

### Real-time Video Analysis
```python
def custom_frame_callback(frame):
    # Custom processing on each frame
    # - Object detection
    # - Motion tracking
    # - Custom overlays
    pass

video_stream.set_frame_callback(custom_frame_callback)
```

### Custom HUD Elements
```python
class CustomHUD(HUDOverlay):
    def apply_hud(self, frame, telemetry_data, flight_status):
        # Call parent HUD
        hud_frame = super().apply_hud(frame, telemetry_data, flight_status)
        
        # Add custom elements
        cv2.putText(hud_frame, "CUSTOM DATA", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        return hud_frame
```

### Flight Path Recording
The system automatically records:
- **GPS coordinates** (if available)
- **Attitude data** (pitch, roll, yaw)
- **Speed vectors** (X, Y, Z components)
- **Sensor readings** (barometer, accelerometer)

This data can be used for:
- **3D flight path visualization**
- **Performance analysis**
- **Training review**
- **Incident investigation**

## 📱 Mobile-Style HUD

The HUD design follows modern aviation and mobile drone app conventions:
- **Green overlay** for normal operations
- **Yellow/Red warnings** for attention/critical states
- **Minimalist design** to avoid cluttering view
- **Context-sensitive information** display
- **High contrast** for outdoor visibility

## 🎓 Best Practices

### Video Operations
1. **Always test video before flight** to ensure proper operation
2. **Monitor recording status** during flight
3. **Keep spare storage space** for recordings
4. **Use HUD for situational awareness** not primary navigation
5. **Practice with HUD elements** before critical flights

### Recording Guidelines
1. **Start recording before takeoff** for complete flight record
2. **Keep recordings organized** by date/mission
3. **Review footage post-flight** for improvement opportunities
4. **Back up important recordings** to prevent data loss
5. **Use telemetry data** for performance analysis

The video and HUD system transforms your P8 Pro into a professional-grade platform with comprehensive visual feedback and recording capabilities!