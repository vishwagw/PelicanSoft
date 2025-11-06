"""
Drone Control Commands for P8 Pro
Implements flight control, movement, and configuration commands
"""

import logging
import time
from typing import Optional, Dict, Any
from enum import Enum

class FlightMode(Enum):
    """Flight modes for the drone"""
    MANUAL = "manual"
    AUTO = "auto"
    LAND = "land"
    TAKEOFF = "takeoff"

class DroneController:
    """High-level drone control interface"""
    
    def __init__(self, connection):
        """
        Initialize drone controller
        
        Args:
            connection: DroneConnection instance
        """
        self.connection = connection
        self.logger = logging.getLogger(__name__)
        
        self.is_flying = False
        self.current_mode = FlightMode.MANUAL
        self.emergency_stop_active = False
        
        # Movement constraints
        self.max_speed = 100  # cm/s
        self.max_altitude = 500  # cm
        self.min_battery = 20  # percent
        
        # Current state
        self.current_battery = 100
        self.current_altitude = 0
        self.current_speed = 0
    
    def initialize(self) -> bool:
        """
        Initialize drone for control
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Enter command mode
            response = self.connection.send_command("command")
            if not response or "ok" not in response.lower():
                self.logger.error("Failed to enter command mode")
                return False
            
            # Enable telemetry
            response = self.connection.send_command("streamon")
            if response and "ok" in response.lower():
                self.logger.info("Telemetry stream enabled")
            
            # Set speed to moderate level
            self.set_speed(50)
            
            self.logger.info("Drone initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
    
    def takeoff(self) -> bool:
        """
        Perform automatic takeoff
        
        Returns:
            bool: True if takeoff successful
        """
        if self.is_flying:
            self.logger.warning("Already flying")
            return False
        
        if self.current_battery < self.min_battery:
            self.logger.error(f"Battery too low for takeoff: {self.current_battery}%")
            return False
        
        try:
            self.logger.info("Initiating takeoff")
            response = self.connection.send_command("takeoff", timeout=10.0)
            
            if response and "ok" in response.lower():
                self.is_flying = True
                self.current_mode = FlightMode.TAKEOFF
                self.logger.info("Takeoff successful")
                
                # Wait for stabilization
                time.sleep(3.0)
                self.current_mode = FlightMode.MANUAL
                return True
            else:
                self.logger.error(f"Takeoff failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Takeoff error: {e}")
            return False
    
    def land(self) -> bool:
        """
        Perform automatic landing
        
        Returns:
            bool: True if landing successful
        """
        if not self.is_flying:
            self.logger.warning("Already landed")
            return False
        
        try:
            self.logger.info("Initiating landing")
            response = self.connection.send_command("land", timeout=15.0)
            
            if response and "ok" in response.lower():
                self.is_flying = False
                self.current_mode = FlightMode.LAND
                self.current_altitude = 0
                self.logger.info("Landing successful")
                return True
            else:
                self.logger.error(f"Landing failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Landing error: {e}")
            return False
    
    def emergency_stop(self) -> bool:
        """
        Emergency stop - immediate motor shutdown
        
        Returns:
            bool: True if emergency stop successful
        """
        try:
            self.emergency_stop_active = True
            self.logger.warning("EMERGENCY STOP ACTIVATED")
            
            response = self.connection.send_command("emergency", timeout=2.0)
            
            self.is_flying = False
            self.current_mode = FlightMode.LAND
            self.current_altitude = 0
            
            return True
            
        except Exception as e:
            self.logger.error(f"Emergency stop error: {e}")
            return False
    
    def move_forward(self, distance: int) -> bool:
        """
        Move forward by specified distance
        
        Args:
            distance: Distance in cm (20-500)
            
        Returns:
            bool: True if movement successful
        """
        return self._move_directional("forward", distance)
    
    def move_backward(self, distance: int) -> bool:
        """
        Move backward by specified distance
        
        Args:
            distance: Distance in cm (20-500)
            
        Returns:
            bool: True if movement successful
        """
        return self._move_directional("back", distance)
    
    def move_left(self, distance: int) -> bool:
        """
        Move left by specified distance
        
        Args:
            distance: Distance in cm (20-500)
            
        Returns:
            bool: True if movement successful
        """
        return self._move_directional("left", distance)
    
    def move_right(self, distance: int) -> bool:
        """
        Move right by specified distance
        
        Args:
            distance: Distance in cm (20-500)
            
        Returns:
            bool: True if movement successful
        """
        return self._move_directional("right", distance)
    
    def move_up(self, distance: int) -> bool:
        """
        Move up by specified distance
        
        Args:
            distance: Distance in cm (20-500)
            
        Returns:
            bool: True if movement successful
        """
        if self.current_altitude + distance > self.max_altitude:
            self.logger.error(f"Altitude limit exceeded: {self.current_altitude + distance}")
            return False
        
        return self._move_directional("up", distance)
    
    def move_down(self, distance: int) -> bool:
        """
        Move down by specified distance
        
        Args:
            distance: Distance in cm (20-500)
            
        Returns:
            bool: True if movement successful
        """
        return self._move_directional("down", distance)
    
    def rotate_clockwise(self, degrees: int) -> bool:
        """
        Rotate clockwise by specified degrees
        
        Args:
            degrees: Rotation in degrees (1-360)
            
        Returns:
            bool: True if rotation successful
        """
        return self._rotate("cw", degrees)
    
    def rotate_counterclockwise(self, degrees: int) -> bool:
        """
        Rotate counterclockwise by specified degrees
        
        Args:
            degrees: Rotation in degrees (1-360)
            
        Returns:
            bool: True if rotation successful
        """
        return self._rotate("ccw", degrees)
    
    def _move_directional(self, direction: str, distance: int) -> bool:
        """
        Internal method for directional movement
        
        Args:
            direction: Movement direction (forward, back, left, right, up, down)
            distance: Distance in cm
            
        Returns:
            bool: True if movement successful
        """
        if not self.is_flying:
            self.logger.error("Cannot move - drone not flying")
            return False
        
        if not 20 <= distance <= 500:
            self.logger.error(f"Invalid distance: {distance}cm (must be 20-500)")
            return False
        
        try:
            command = f"{direction} {distance}"
            self.logger.info(f"Moving {direction} {distance}cm")
            
            response = self.connection.send_command(command, timeout=8.0)
            
            if response and "ok" in response.lower():
                if direction == "up":
                    self.current_altitude += distance
                elif direction == "down":
                    self.current_altitude = max(0, self.current_altitude - distance)
                
                self.logger.info(f"Movement successful: {command}")
                return True
            else:
                self.logger.error(f"Movement failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Movement error: {e}")
            return False
    
    def _rotate(self, direction: str, degrees: int) -> bool:
        """
        Internal method for rotation
        
        Args:
            direction: Rotation direction (cw, ccw)
            degrees: Rotation in degrees
            
        Returns:
            bool: True if rotation successful
        """
        if not self.is_flying:
            self.logger.error("Cannot rotate - drone not flying")
            return False
        
        if not 1 <= degrees <= 360:
            self.logger.error(f"Invalid degrees: {degrees} (must be 1-360)")
            return False
        
        try:
            command = f"{direction} {degrees}"
            self.logger.info(f"Rotating {direction} {degrees} degrees")
            
            response = self.connection.send_command(command, timeout=5.0)
            
            if response and "ok" in response.lower():
                self.logger.info(f"Rotation successful: {command}")
                return True
            else:
                self.logger.error(f"Rotation failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Rotation error: {e}")
            return False
    
    def set_speed(self, speed: int) -> bool:
        """
        Set movement speed
        
        Args:
            speed: Speed value (10-100)
            
        Returns:
            bool: True if speed set successfully
        """
        if not 10 <= speed <= 100:
            self.logger.error(f"Invalid speed: {speed} (must be 10-100)")
            return False
        
        try:
            command = f"speed {speed}"
            response = self.connection.send_command(command)
            
            if response and "ok" in response.lower():
                self.current_speed = speed
                self.logger.info(f"Speed set to {speed}")
                return True
            else:
                self.logger.error(f"Failed to set speed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Set speed error: {e}")
            return False
    
    def hover(self, duration: float = 1.0):
        """
        Hover in place for specified duration
        
        Args:
            duration: Hover duration in seconds
        """
        if self.is_flying:
            self.logger.info(f"Hovering for {duration} seconds")
            time.sleep(duration)
    
    def get_battery_level(self) -> Optional[int]:
        """
        Get current battery level
        
        Returns:
            int: Battery percentage or None if unavailable
        """
        try:
            response = self.connection.send_command("battery?")
            if response and response.isdigit():
                self.current_battery = int(response)
                return self.current_battery
            return None
        except Exception as e:
            self.logger.error(f"Battery check error: {e}")
            return None
    
    def get_flight_status(self) -> Dict[str, Any]:
        """
        Get comprehensive flight status
        
        Returns:
            dict: Flight status information
        """
        return {
            "is_flying": self.is_flying,
            "mode": self.current_mode.value,
            "battery": self.current_battery,
            "altitude": self.current_altitude,
            "speed": self.current_speed,
            "emergency_stop": self.emergency_stop_active,
            "connected": self.connection.is_connected
        }
    
    # Camera Control Methods
    
    def start_video_stream(self) -> bool:
        """
        Start video streaming
        
        Returns:
            bool: True if video stream started successfully
        """
        try:
            response = self.connection.send_command("streamon")
            if response and "ok" in response.lower():
                self.logger.info("Video stream started")
                return True
            else:
                self.logger.error(f"Failed to start video stream: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error starting video stream: {e}")
            return False
    
    def stop_video_stream(self) -> bool:
        """
        Stop video streaming
        
        Returns:
            bool: True if video stream stopped successfully
        """
        try:
            response = self.connection.send_command("streamoff")
            if response and "ok" in response.lower():
                self.logger.info("Video stream stopped")
                return True
            else:
                self.logger.error(f"Failed to stop video stream: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error stopping video stream: {e}")
            return False
    
    def set_video_bitrate(self, bitrate: int) -> bool:
        """
        Set video bitrate
        
        Args:
            bitrate: Video bitrate (1-5)
            
        Returns:
            bool: True if bitrate set successfully
        """
        if not 1 <= bitrate <= 5:
            self.logger.error(f"Invalid bitrate: {bitrate} (must be 1-5)")
            return False
        
        try:
            command = f"setbitrate {bitrate}"
            response = self.connection.send_command(command)
            
            if response and "ok" in response.lower():
                self.logger.info(f"Video bitrate set to {bitrate}")
                return True
            else:
                self.logger.error(f"Failed to set bitrate: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error setting bitrate: {e}")
            return False
    
    def set_video_resolution(self, resolution: str) -> bool:
        """
        Set video resolution
        
        Args:
            resolution: Resolution setting ("high" or "low")
            
        Returns:
            bool: True if resolution set successfully
        """
        if resolution not in ["high", "low"]:
            self.logger.error(f"Invalid resolution: {resolution} (must be 'high' or 'low')")
            return False
        
        try:
            command = f"setresolution {resolution}"
            response = self.connection.send_command(command)
            
            if response and "ok" in response.lower():
                self.logger.info(f"Video resolution set to {resolution}")
                return True
            else:
                self.logger.error(f"Failed to set resolution: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error setting resolution: {e}")
            return False
    
    def set_video_fps(self, fps: str) -> bool:
        """
        Set video frame rate
        
        Args:
            fps: Frame rate setting ("high", "middle", "low")
            
        Returns:
            bool: True if FPS set successfully
        """
        if fps not in ["high", "middle", "low"]:
            self.logger.error(f"Invalid FPS: {fps} (must be 'high', 'middle', or 'low')")
            return False
        
        try:
            command = f"setfps {fps}"
            response = self.connection.send_command(command)
            
            if response and "ok" in response.lower():
                self.logger.info(f"Video FPS set to {fps}")
                return True
            else:
                self.logger.error(f"Failed to set FPS: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error setting FPS: {e}")
            return False