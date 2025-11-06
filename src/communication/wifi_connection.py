"""
WiFi Communication Module for P8 Pro Drone
Handles UDP/TCP connections and command protocol
"""

import socket
import threading
import time
import logging
from typing import Optional, Callable, Dict, Any
from queue import Queue, Empty

class DroneConnection:
    """Manages WiFi connection to P8 Pro drone"""
    
    def __init__(self, drone_ip: str = "192.168.1.1", command_port: int = 8889, 
                 state_port: int = 8890, video_port: int = 11111):
        """
        Initialize drone connection
        
        Args:
            drone_ip: IP address of the drone
            command_port: Port for sending commands
            state_port: Port for receiving telemetry
            video_port: Port for video stream (future use)
        """
        self.drone_ip = drone_ip
        self.command_port = command_port
        self.state_port = state_port
        self.video_port = video_port
        
        self.command_socket: Optional[socket.socket] = None
        self.state_socket: Optional[socket.socket] = None
        
        self.is_connected = False
        self.is_listening = False
        
        self.command_queue = Queue()
        self.response_queue = Queue()
        self.telemetry_queue = Queue()
        
        self.command_thread: Optional[threading.Thread] = None
        self.state_thread: Optional[threading.Thread] = None
        
        self.telemetry_callback: Optional[Callable] = None
        self.connection_callback: Optional[Callable] = None
        
        self.logger = logging.getLogger(__name__)
        
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 5.0  # seconds
        
    def connect(self) -> bool:
        """
        Establish connection to drone
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Create command socket (UDP)
            self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.command_socket.settimeout(5.0)
            
            # Create state socket (UDP)
            self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.state_socket.bind(('', self.state_port))
            self.state_socket.settimeout(1.0)
            
            # Test connection with command
            test_response = self.send_command("command", timeout=3.0)
            if test_response and "ok" in test_response.lower():
                self.is_connected = True
                self.is_listening = True
                
                # Start communication threads
                self.start_communication_threads()
                
                self.logger.info(f"Connected to drone at {self.drone_ip}")
                if self.connection_callback:
                    self.connection_callback(True)
                
                return True
            else:
                self.logger.error("Failed to establish communication with drone")
                self.disconnect()
                return False
                
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from drone and cleanup resources"""
        self.is_connected = False
        self.is_listening = False
        
        # Close sockets
        if self.command_socket:
            self.command_socket.close()
            self.command_socket = None
            
        if self.state_socket:
            self.state_socket.close()
            self.state_socket = None
        
        # Wait for threads to finish
        if self.command_thread and self.command_thread.is_alive():
            self.command_thread.join(timeout=2.0)
            
        if self.state_thread and self.state_thread.is_alive():
            self.state_thread.join(timeout=2.0)
        
        if self.connection_callback:
            self.connection_callback(False)
            
        self.logger.info("Disconnected from drone")
    
    def start_communication_threads(self):
        """Start background threads for command processing and telemetry"""
        # Command processing thread
        self.command_thread = threading.Thread(target=self._command_processor, daemon=True)
        self.command_thread.start()
        
        # Telemetry listening thread
        self.state_thread = threading.Thread(target=self._telemetry_listener, daemon=True)
        self.state_thread.start()
        
        # Heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
        heartbeat_thread.start()
    
    def send_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """
        Send command to drone and wait for response
        
        Args:
            command: Command string to send
            timeout: Response timeout in seconds
            
        Returns:
            str: Response from drone or None if timeout
        """
        if not self.is_connected or not self.command_socket:
            self.logger.warning("Cannot send command - not connected")
            return None
        
        try:
            # Send command
            self.command_socket.sendto(command.encode('utf-8'), 
                                     (self.drone_ip, self.command_port))
            self.logger.debug(f"Sent command: {command}")
            
            # Wait for response
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, _ = self.command_socket.recvfrom(1024)
                    response = data.decode('utf-8').strip()
                    self.logger.debug(f"Received response: {response}")
                    return response
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"Error receiving response: {e}")
                    break
            
            self.logger.warning(f"Command timeout: {command}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error sending command '{command}': {e}")
            return None
    
    def send_command_async(self, command: str):
        """
        Send command asynchronously (fire and forget)
        
        Args:
            command: Command string to send
        """
        if self.is_connected:
            self.command_queue.put(command)
    
    def _command_processor(self):
        """Background thread for processing asynchronous commands"""
        while self.is_listening:
            try:
                command = self.command_queue.get(timeout=0.1)
                response = self.send_command(command)
                if response:
                    self.response_queue.put((command, response))
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Command processor error: {e}")
    
    def _telemetry_listener(self):
        """Background thread for receiving telemetry data"""
        while self.is_listening:
            try:
                if self.state_socket:
                    data, _ = self.state_socket.recvfrom(1024)
                    telemetry = data.decode('utf-8').strip()
                    
                    if telemetry:
                        self.telemetry_queue.put(telemetry)
                        if self.telemetry_callback:
                            self.telemetry_callback(telemetry)
                        
                        self.last_heartbeat = time.time()
                        
            except socket.timeout:
                continue
            except Exception as e:
                self.logger.error(f"Telemetry listener error: {e}")
    
    def _heartbeat_monitor(self):
        """Monitor connection health via heartbeat"""
        while self.is_listening:
            try:
                if time.time() - self.last_heartbeat > self.heartbeat_interval * 2:
                    self.logger.warning("Heartbeat timeout - connection may be lost")
                    # Try to re-establish connection
                    if not self.send_command("command", timeout=1.0):
                        self.logger.error("Lost connection to drone")
                        self.disconnect()
                        break
                
                time.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"Heartbeat monitor error: {e}")
    
    def set_telemetry_callback(self, callback: Callable[[str], None]):
        """Set callback function for telemetry data"""
        self.telemetry_callback = callback
    
    def set_connection_callback(self, callback: Callable[[bool], None]):
        """Set callback function for connection status changes"""
        self.connection_callback = callback
    
    def get_latest_telemetry(self) -> Optional[str]:
        """Get most recent telemetry data"""
        try:
            return self.telemetry_queue.get_nowait()
        except Empty:
            return None
    
    def get_latest_response(self) -> Optional[tuple]:
        """Get most recent command response"""
        try:
            return self.response_queue.get_nowait()
        except Empty:
            return None