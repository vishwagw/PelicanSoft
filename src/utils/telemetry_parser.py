"""
Telemetry Parser for P8 Pro Drone
Parses incoming telemetry data and extracts relevant information
"""

import re
import logging
from typing import Dict, Any, Optional

class TelemetryParser:
    """Parses drone telemetry data into structured format"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Regex patterns for common telemetry data
        self.patterns = {
            'battery': re.compile(r'bat:(\d+)'),
            'altitude': re.compile(r'h:(\d+)'),
            'speed': re.compile(r'vg([xyz]):(-?\d+)'),
            'temperature': re.compile(r'temp:(\d+)'),
            'attitude': re.compile(r'pitch:(-?\d+);roll:(-?\d+);yaw:(-?\d+)'),
            'acceleration': re.compile(r'ag([xyz]):(-?\d+\.\d+)'),
            'barometer': re.compile(r'baro:(-?\d+\.\d+)'),
            'time_of_flight': re.compile(r'tof:(\d+)'),
            'motor_time': re.compile(r'time:(\d+)')
        }
    
    def parse(self, telemetry_string: str) -> Dict[str, Any]:
        """
        Parse telemetry string into structured data
        
        Args:
            telemetry_string: Raw telemetry data from drone
            
        Returns:
            dict: Parsed telemetry data
        """
        parsed_data = {}
        
        try:
            # Clean the telemetry string
            telemetry_string = telemetry_string.strip()
            
            # Extract battery level
            battery_match = self.patterns['battery'].search(telemetry_string)
            if battery_match:
                parsed_data['battery'] = int(battery_match.group(1))
            
            # Extract altitude
            altitude_match = self.patterns['altitude'].search(telemetry_string)
            if altitude_match:
                parsed_data['altitude'] = int(altitude_match.group(1))
            
            # Extract speed components
            speed_matches = self.patterns['speed'].findall(telemetry_string)
            if speed_matches:
                speeds = {}
                for axis, speed in speed_matches:
                    speeds[f'speed_{axis}'] = int(speed)
                parsed_data.update(speeds)
                
                # Calculate total speed
                if 'speed_x' in speeds and 'speed_y' in speeds:
                    total_speed = (speeds['speed_x']**2 + speeds['speed_y']**2)**0.5
                    parsed_data['speed_total'] = round(total_speed, 2)
            
            # Extract temperature
            temp_match = self.patterns['temperature'].search(telemetry_string)
            if temp_match:
                parsed_data['temperature'] = int(temp_match.group(1))
            
            # Extract attitude (pitch, roll, yaw)
            attitude_match = self.patterns['attitude'].search(telemetry_string)
            if attitude_match:
                parsed_data['pitch'] = int(attitude_match.group(1))
                parsed_data['roll'] = int(attitude_match.group(2))
                parsed_data['yaw'] = int(attitude_match.group(3))
            
            # Extract acceleration
            accel_matches = self.patterns['acceleration'].findall(telemetry_string)
            if accel_matches:
                for axis, accel in accel_matches:
                    parsed_data[f'acceleration_{axis}'] = float(accel)
            
            # Extract barometer reading
            baro_match = self.patterns['barometer'].search(telemetry_string)
            if baro_match:
                parsed_data['barometer'] = float(baro_match.group(1))
            
            # Extract time of flight sensor
            tof_match = self.patterns['time_of_flight'].search(telemetry_string)
            if tof_match:
                parsed_data['time_of_flight'] = int(tof_match.group(1))
            
            # Extract motor time
            motor_time_match = self.patterns['motor_time'].search(telemetry_string)
            if motor_time_match:
                parsed_data['motor_time'] = int(motor_time_match.group(1))
            
            # Add timestamp
            import time
            parsed_data['timestamp'] = time.time()
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Error parsing telemetry: {e}")
            return {}
    
    def format_for_display(self, parsed_data: Dict[str, Any]) -> str:
        """
        Format parsed data for human-readable display
        
        Args:
            parsed_data: Parsed telemetry dictionary
            
        Returns:
            str: Formatted string for display
        """
        lines = []
        
        # Essential flight data
        if 'battery' in parsed_data:
            lines.append(f"Battery: {parsed_data['battery']}%")
        
        if 'altitude' in parsed_data:
            lines.append(f"Altitude: {parsed_data['altitude']} cm")
        
        if 'speed_total' in parsed_data:
            lines.append(f"Speed: {parsed_data['speed_total']} cm/s")
        
        # Attitude information
        if all(key in parsed_data for key in ['pitch', 'roll', 'yaw']):
            lines.append(f"Attitude: P:{parsed_data['pitch']}° R:{parsed_data['roll']}° Y:{parsed_data['yaw']}°")
        
        # Temperature
        if 'temperature' in parsed_data:
            lines.append(f"Temperature: {parsed_data['temperature']}°C")
        
        # Time of flight sensor
        if 'time_of_flight' in parsed_data:
            lines.append(f"Distance below: {parsed_data['time_of_flight']} cm")
        
        return " | ".join(lines) if lines else "No telemetry data"
    
    def get_critical_alerts(self, parsed_data: Dict[str, Any]) -> list:
        """
        Check for critical conditions that require attention
        
        Args:
            parsed_data: Parsed telemetry dictionary
            
        Returns:
            list: List of alert messages
        """
        alerts = []
        
        # Low battery warning
        if 'battery' in parsed_data and parsed_data['battery'] < 20:
            alerts.append(f"LOW BATTERY: {parsed_data['battery']}%")
        
        # Very low battery critical
        if 'battery' in parsed_data and parsed_data['battery'] < 10:
            alerts.append(f"CRITICAL BATTERY: {parsed_data['battery']}% - LAND IMMEDIATELY")
        
        # High temperature warning
        if 'temperature' in parsed_data and parsed_data['temperature'] > 80:
            alerts.append(f"HIGH TEMPERATURE: {parsed_data['temperature']}°C")
        
        # Extreme attitude warnings
        if 'pitch' in parsed_data and abs(parsed_data['pitch']) > 45:
            alerts.append(f"EXTREME PITCH: {parsed_data['pitch']}°")
        
        if 'roll' in parsed_data and abs(parsed_data['roll']) > 45:
            alerts.append(f"EXTREME ROLL: {parsed_data['roll']}°")
        
        # Low altitude warning (too close to ground)
        if 'time_of_flight' in parsed_data and parsed_data['time_of_flight'] < 20:
            alerts.append(f"LOW ALTITUDE: {parsed_data['time_of_flight']} cm")
        
        return alerts