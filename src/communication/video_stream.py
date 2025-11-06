"""
Video Streaming Module for P8 Pro Drone Camera
Handles video stream reception, decoding, and display with HUD overlay
"""

import cv2
import numpy as np
import threading
import socket
import time
import logging
from typing import Optional, Callable, Tuple, Dict, Any
from queue import Queue, Empty
import struct

class VideoStream:
    """Manages video streaming from P8 Pro drone camera"""
    
    def __init__(self, drone_ip: str = "192.168.1.1", video_port: int = 11111):
        """
        Initialize video stream
        
        Args:
            drone_ip: IP address of the drone
            video_port: Port for video stream
        """
        self.drone_ip = drone_ip
        self.video_port = video_port
        
        self.video_socket: Optional[socket.socket] = None
        self.is_streaming = False
        self.stream_thread: Optional[threading.Thread] = None
        
        self.frame_queue = Queue(maxsize=10)
        self.latest_frame: Optional[np.ndarray] = None
        
        self.frame_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        
        self.logger = logging.getLogger(__name__)
        
        # Video statistics
        self.frames_received = 0
        self.frames_dropped = 0
        self.last_frame_time = 0
        self.fps = 0
        
        # Video settings
        self.target_resolution = (960, 720)  # P8 Pro typical resolution
        self.frame_rate = 30
        
    def start_stream(self) -> bool:
        """
        Start video streaming
        
        Returns:
            bool: True if stream started successfully
        """
        if self.is_streaming:
            self.logger.warning("Video stream already running")
            return True
        
        try:
            # Create video socket
            self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.video_socket.bind(('', self.video_port))
            self.video_socket.settimeout(1.0)
            
            self.is_streaming = True
            
            # Start streaming thread
            self.stream_thread = threading.Thread(target=self._stream_receiver, daemon=True)
            self.stream_thread.start()
            
            self.logger.info(f"Video stream started on port {self.video_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start video stream: {e}")
            self.stop_stream()
            return False
    
    def stop_stream(self):
        """Stop video streaming"""
        self.is_streaming = False
        
        if self.video_socket:
            self.video_socket.close()
            self.video_socket = None
        
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        
        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Empty:
                break
        
        self.logger.info("Video stream stopped")
    
    def _stream_receiver(self):
        """Background thread for receiving video stream"""
        buffer = b''
        
        while self.is_streaming:
            try:
                if self.video_socket:
                    data, _ = self.video_socket.recvfrom(2048)
                    
                    if data:
                        buffer += data
                        
                        # Try to decode frame from buffer
                        frame = self._decode_frame(buffer)
                        if frame is not None:
                            self._process_frame(frame)
                            buffer = b''  # Clear buffer after successful decode
                        
                        # Prevent buffer overflow
                        if len(buffer) > 100000:  # 100KB limit
                            buffer = buffer[-50000:]  # Keep last 50KB
                            
            except socket.timeout:
                continue
            except Exception as e:
                self.logger.error(f"Video stream error: {e}")
                if self.error_callback:
                    self.error_callback(e)
                time.sleep(0.1)
    
    def _decode_frame(self, data: bytes) -> Optional[np.ndarray]:
        """
        Decode video frame from raw data
        
        Args:
            data: Raw video data
            
        Returns:
            numpy.ndarray: Decoded frame or None if failed
        """
        try:
            # Try to decode as JPEG first (common for drone cameras)
            if data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9'):
                # Complete JPEG frame
                frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    return frame
            
            # Try H.264 decoding (if available)
            # This is more complex and may require additional libraries
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Frame decode error: {e}")
            return None
    
    def _process_frame(self, frame: np.ndarray):
        """
        Process received frame
        
        Args:
            frame: Decoded video frame
        """
        current_time = time.time()
        
        # Update statistics
        self.frames_received += 1
        if self.last_frame_time > 0:
            frame_interval = current_time - self.last_frame_time
            if frame_interval > 0:
                self.fps = 1.0 / frame_interval
        self.last_frame_time = current_time
        
        # Resize frame if needed
        if frame.shape[:2] != self.target_resolution[::-1]:
            frame = cv2.resize(frame, self.target_resolution)
        
        # Store latest frame
        self.latest_frame = frame.copy()
        
        # Add to queue (drop old frames if queue is full)
        try:
            self.frame_queue.put_nowait(frame)
        except:
            # Queue full, drop oldest frame
            try:
                self.frame_queue.get_nowait()
                self.frame_queue.put_nowait(frame)
                self.frames_dropped += 1
            except Empty:
                pass
        
        # Call frame callback
        if self.frame_callback:
            try:
                self.frame_callback(frame)
            except Exception as e:
                self.logger.error(f"Frame callback error: {e}")
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame
        
        Returns:
            numpy.ndarray: Latest frame or None if no frame available
        """
        return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def get_frame_from_queue(self) -> Optional[np.ndarray]:
        """
        Get frame from queue (blocking)
        
        Returns:
            numpy.ndarray: Frame from queue or None if timeout
        """
        try:
            return self.frame_queue.get(timeout=0.1)
        except Empty:
            return None
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """Set callback function for new frames"""
        self.frame_callback = callback
    
    def set_error_callback(self, callback: Callable[[Exception], None]):
        """Set callback function for stream errors"""
        self.error_callback = callback
    
    def get_stream_stats(self) -> Dict[str, Any]:
        """
        Get video stream statistics
        
        Returns:
            dict: Stream statistics
        """
        return {
            'is_streaming': self.is_streaming,
            'frames_received': self.frames_received,
            'frames_dropped': self.frames_dropped,
            'fps': round(self.fps, 1),
            'resolution': self.target_resolution,
            'frame_available': self.latest_frame is not None
        }


class HUDOverlay:
    """Creates HUD overlay on video stream"""
    
    def __init__(self):
        """Initialize HUD overlay"""
        self.logger = logging.getLogger(__name__)
        
        # HUD settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
        self.text_color = (0, 255, 0)  # Green
        self.bg_color = (0, 0, 0)  # Black background
        self.warning_color = (0, 0, 255)  # Red for warnings
        self.critical_color = (0, 0, 255)  # Red for critical
        
        # HUD elements positioning
        self.hud_enabled = True
        self.show_telemetry = True
        self.show_crosshair = True
        self.show_horizon = True
        self.show_compass = True
        
    def apply_hud(self, frame: np.ndarray, telemetry_data: Dict[str, Any], 
                  flight_status: Dict[str, Any]) -> np.ndarray:
        """
        Apply HUD overlay to video frame
        
        Args:
            frame: Video frame
            telemetry_data: Parsed telemetry data
            flight_status: Flight status information
            
        Returns:
            numpy.ndarray: Frame with HUD overlay
        """
        if not self.hud_enabled or frame is None:
            return frame
        
        hud_frame = frame.copy()
        height, width = hud_frame.shape[:2]
        
        # Draw HUD elements
        if self.show_crosshair:
            self._draw_crosshair(hud_frame, width, height)
        
        if self.show_telemetry:
            self._draw_telemetry(hud_frame, telemetry_data, flight_status, width, height)
        
        if self.show_horizon and 'pitch' in telemetry_data and 'roll' in telemetry_data:
            self._draw_artificial_horizon(hud_frame, telemetry_data['pitch'], 
                                        telemetry_data['roll'], width, height)
        
        if self.show_compass and 'yaw' in telemetry_data:
            self._draw_compass(hud_frame, telemetry_data['yaw'], width, height)
        
        return hud_frame
    
    def _draw_crosshair(self, frame: np.ndarray, width: int, height: int):
        """Draw center crosshair"""
        center_x, center_y = width // 2, height // 2
        cross_size = 20
        
        # Horizontal line
        cv2.line(frame, (center_x - cross_size, center_y), 
                (center_x + cross_size, center_y), self.text_color, 2)
        
        # Vertical line
        cv2.line(frame, (center_x, center_y - cross_size), 
                (center_x, center_y + cross_size), self.text_color, 2)
        
        # Center dot
        cv2.circle(frame, (center_x, center_y), 3, self.text_color, -1)
    
    def _draw_telemetry(self, frame: np.ndarray, telemetry_data: Dict[str, Any], 
                       flight_status: Dict[str, Any], width: int, height: int):
        """Draw telemetry information"""
        y_offset = 30
        line_height = 25
        
        # Battery (top left)
        battery = telemetry_data.get('battery', flight_status.get('battery', 0))
        color = self._get_battery_color(battery)
        self._draw_text_with_bg(frame, f"BAT: {battery}%", (10, y_offset), color)
        
        # Altitude (top left)
        altitude = telemetry_data.get('altitude', flight_status.get('altitude', 0))
        self._draw_text_with_bg(frame, f"ALT: {altitude}cm", (10, y_offset + line_height))
        
        # Speed (top left)
        speed = telemetry_data.get('speed_total', 0)
        self._draw_text_with_bg(frame, f"SPD: {speed:.1f}cm/s", (10, y_offset + 2 * line_height))
        
        # Flight mode (top left)
        mode = flight_status.get('mode', 'Unknown')
        self._draw_text_with_bg(frame, f"MODE: {mode}", (10, y_offset + 3 * line_height))
        
        # GPS coordinates (if available)
        if 'gps_lat' in telemetry_data and 'gps_lon' in telemetry_data:
            gps_text = f"GPS: {telemetry_data['gps_lat']:.6f}, {telemetry_data['gps_lon']:.6f}"
            self._draw_text_with_bg(frame, gps_text, (10, height - 60))
        
        # Temperature (top right)
        if 'temperature' in telemetry_data:
            temp = telemetry_data['temperature']
            temp_color = self.warning_color if temp > 70 else self.text_color
            self._draw_text_with_bg(frame, f"TEMP: {temp}°C", (width - 150, y_offset), temp_color)
        
        # Time of flight sensor (top right)
        if 'time_of_flight' in telemetry_data:
            tof = telemetry_data['time_of_flight']
            tof_color = self.warning_color if tof < 30 else self.text_color
            self._draw_text_with_bg(frame, f"TOF: {tof}cm", (width - 150, y_offset + line_height), tof_color)
        
        # Flight time (bottom right)
        flight_time = flight_status.get('flight_time', 0)
        if flight_time > 0:
            minutes = int(flight_time // 60)
            seconds = int(flight_time % 60)
            self._draw_text_with_bg(frame, f"TIME: {minutes:02d}:{seconds:02d}", 
                                  (width - 150, height - 30))
    
    def _draw_artificial_horizon(self, frame: np.ndarray, pitch: float, roll: float, 
                               width: int, height: int):
        """Draw artificial horizon"""
        center_x, center_y = width // 2, height // 2
        horizon_width = 200
        horizon_height = 100
        
        # Draw horizon background
        horizon_rect = (center_x - horizon_width//2, center_y - horizon_height//2,
                       horizon_width, horizon_height)
        
        # Calculate horizon line based on pitch and roll
        pitch_offset = int(pitch * 2)  # Scale pitch
        roll_rad = np.radians(roll)
        
        # Horizon line endpoints
        x1 = center_x - horizon_width//2
        x2 = center_x + horizon_width//2
        y1 = center_y - pitch_offset + int((x1 - center_x) * np.tan(roll_rad))
        y2 = center_y - pitch_offset + int((x2 - center_x) * np.tan(roll_rad))
        
        # Draw horizon line
        cv2.line(frame, (x1, y1), (x2, y2), self.text_color, 3)
        
        # Draw attitude indicator
        cv2.rectangle(frame, (center_x - 2, center_y - 10), 
                     (center_x + 2, center_y + 10), self.text_color, -1)
    
    def _draw_compass(self, frame: np.ndarray, yaw: float, width: int, height: int):
        """Draw compass heading"""
        center_x = width // 2
        compass_y = 50
        compass_width = 200
        
        # Draw compass background
        cv2.rectangle(frame, (center_x - compass_width//2, compass_y - 15),
                     (center_x + compass_width//2, compass_y + 15), 
                     self.bg_color, -1)
        
        # Draw heading marks
        for i in range(-90, 91, 30):
            mark_x = center_x + int(i * compass_width / 180)
            heading = (yaw + i) % 360
            
            if i == 0:  # Current heading
                cv2.line(frame, (mark_x, compass_y - 10), (mark_x, compass_y + 10), 
                        self.text_color, 3)
                self._draw_text_with_bg(frame, f"{int(heading)}°", 
                                      (mark_x - 15, compass_y - 20))
            else:
                cv2.line(frame, (mark_x, compass_y - 5), (mark_x, compass_y + 5), 
                        self.text_color, 1)
    
    def _draw_text_with_bg(self, frame: np.ndarray, text: str, position: Tuple[int, int], 
                          color: Tuple[int, int, int] = None):
        """Draw text with background for better visibility"""
        if color is None:
            color = self.text_color
        
        x, y = position
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, self.font, self.font_scale, self.font_thickness)
        
        # Draw background rectangle
        cv2.rectangle(frame, (x - 2, y - text_height - 2), 
                     (x + text_width + 2, y + baseline + 2), 
                     self.bg_color, -1)
        
        # Draw text
        cv2.putText(frame, text, (x, y), self.font, self.font_scale, 
                   color, self.font_thickness)
    
    def _get_battery_color(self, battery: int) -> Tuple[int, int, int]:
        """Get color based on battery level"""
        if battery <= 10:
            return self.critical_color
        elif battery <= 20:
            return self.warning_color
        else:
            return self.text_color
    
    def toggle_hud(self):
        """Toggle HUD on/off"""
        self.hud_enabled = not self.hud_enabled
    
    def toggle_element(self, element: str):
        """Toggle specific HUD element"""
        if element == 'crosshair':
            self.show_crosshair = not self.show_crosshair
        elif element == 'telemetry':
            self.show_telemetry = not self.show_telemetry
        elif element == 'horizon':
            self.show_horizon = not self.show_horizon
        elif element == 'compass':
            self.show_compass = not self.show_compass