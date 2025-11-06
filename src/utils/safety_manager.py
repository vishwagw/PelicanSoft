"""
Safety Manager for P8 Pro Drone Controller
Implements safety features including emergency stop, automatic landing, and monitoring
"""

import threading
import time
import logging
from typing import Optional, Callable, Dict, Any
from enum import Enum

class SafetyLevel(Enum):
    """Safety alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class SafetyManager:
    """Manages drone safety features and monitoring"""
    
    def __init__(self, controller, config: Dict[str, Any]):
        """
        Initialize safety manager
        
        Args:
            controller: DroneController instance
            config: Configuration dictionary
        """
        self.controller = controller
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Safety state
        self.safety_enabled = True
        self.emergency_stop_triggered = False
        self.auto_landing_triggered = False
        
        # Monitoring threads
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # Safety thresholds from config
        self.min_battery_flight = config.get('safety', {}).get('min_battery_level', 20)
        self.critical_battery = config.get('safety', {}).get('auto_land_battery_threshold', 10)
        self.max_flight_time = config.get('safety', {}).get('max_flight_time', 1200)
        self.connection_timeout = config.get('network', {}).get('connection_timeout', 5.0)
        
        # Monitoring data
        self.flight_start_time = None
        self.last_telemetry_time = time.time()
        self.last_heartbeat_time = time.time()
        
        # Callbacks
        self.safety_alert_callback: Optional[Callable] = None
        self.emergency_callback: Optional[Callable] = None
        
        # Safety history
        self.safety_events = []
        
        self.logger.info("Safety manager initialized")
    
    def start_monitoring(self):
        """Start safety monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._safety_monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Safety monitoring started")
    
    def stop_monitoring(self):
        """Stop safety monitoring"""
        self.monitoring_active = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        
        self.logger.info("Safety monitoring stopped")
    
    def _safety_monitor_loop(self):
        """Main safety monitoring loop"""
        while self.monitoring_active:
            try:
                if self.safety_enabled:
                    self._check_battery_safety()
                    self._check_flight_time_safety()
                    self._check_connection_safety()
                    self._check_altitude_safety()
                    self._check_emergency_conditions()
                
                time.sleep(1.0)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Safety monitor error: {e}")
                time.sleep(1.0)
    
    def _check_battery_safety(self):
        """Check battery levels and take action if needed"""
        if not self.controller or not self.controller.is_flying:
            return
        
        battery_level = self.controller.current_battery
        
        if battery_level <= self.critical_battery and not self.auto_landing_triggered:
            self.auto_landing_triggered = True
            self._trigger_safety_event(
                SafetyLevel.EMERGENCY,
                f"Critical battery level: {battery_level}%",
                "auto_land"
            )
            
            # Initiate emergency landing
            threading.Thread(target=self._emergency_land, 
                           args=("Critical battery level",), daemon=True).start()
        
        elif battery_level <= self.min_battery_flight:
            self._trigger_safety_event(
                SafetyLevel.WARNING,
                f"Low battery warning: {battery_level}%",
                "warning"
            )
    
    def _check_flight_time_safety(self):
        """Check flight time limits"""
        if not self.controller or not self.controller.is_flying or not self.flight_start_time:
            return
        
        flight_duration = time.time() - self.flight_start_time
        
        if flight_duration >= self.max_flight_time:
            self._trigger_safety_event(
                SafetyLevel.CRITICAL,
                f"Maximum flight time exceeded: {flight_duration:.0f}s",
                "auto_land"
            )
            
            # Force landing
            threading.Thread(target=self._emergency_land, 
                           args=("Flight time limit exceeded",), daemon=True).start()
        
        elif flight_duration >= self.max_flight_time * 0.8:  # 80% warning
            self._trigger_safety_event(
                SafetyLevel.WARNING,
                f"Flight time warning: {flight_duration:.0f}s of {self.max_flight_time}s",
                "warning"
            )
    
    def _check_connection_safety(self):
        """Check connection status and take action if lost"""
        if not self.controller:
            return
        
        connection_lost = not self.controller.connection.is_connected
        time_since_heartbeat = time.time() - self.last_heartbeat_time
        
        if connection_lost or time_since_heartbeat > self.connection_timeout * 2:
            if self.controller.is_flying:
                self._trigger_safety_event(
                    SafetyLevel.CRITICAL,
                    "Connection lost during flight",
                    "connection_loss"
                )
                
                # Execute connection loss action
                action = self.config.get('safety', {}).get('connection_timeout_action', 'land')
                if action == 'land':
                    threading.Thread(target=self._emergency_land, 
                                   args=("Connection lost",), daemon=True).start()
                elif action == 'hover':
                    self.logger.warning("Connection lost - drone will hover")
    
    def _check_altitude_safety(self):
        """Check altitude safety limits"""
        if not self.controller or not self.controller.is_flying:
            return
        
        max_altitude = self.config.get('flight', {}).get('max_altitude', 500)
        current_altitude = self.controller.current_altitude
        
        if current_altitude > max_altitude:
            self._trigger_safety_event(
                SafetyLevel.WARNING,
                f"Altitude limit exceeded: {current_altitude}cm > {max_altitude}cm",
                "altitude_limit"
            )
    
    def _check_emergency_conditions(self):
        """Check for emergency conditions requiring immediate action"""
        if not self.controller:
            return
        
        # Check for extreme battery drain
        if self.controller.current_battery <= 5:
            self.trigger_emergency_stop("Critically low battery - immediate landing required")
        
        # Add more emergency condition checks here
        # - Extreme weather detection
        # - Sensor failures
        # - Communication errors
    
    def trigger_emergency_stop(self, reason: str = "Emergency stop activated") -> bool:
        """
        Trigger emergency stop
        
        Args:
            reason: Reason for emergency stop
            
        Returns:
            bool: True if emergency stop successful
        """
        if self.emergency_stop_triggered:
            return True
        
        self.emergency_stop_triggered = True
        
        self._trigger_safety_event(
            SafetyLevel.EMERGENCY,
            reason,
            "emergency_stop"
        )
        
        self.logger.critical(f"EMERGENCY STOP: {reason}")
        
        # Execute emergency stop
        try:
            if self.controller:
                success = self.controller.emergency_stop()
                
                if success:
                    self.logger.info("Emergency stop executed successfully")
                    return True
                else:
                    self.logger.error("Emergency stop failed")
                    return False
            else:
                self.logger.error("No controller available for emergency stop")
                return False
                
        except Exception as e:
            self.logger.error(f"Emergency stop error: {e}")
            return False
    
    def _emergency_land(self, reason: str):
        """
        Execute emergency landing
        
        Args:
            reason: Reason for emergency landing
        """
        self.logger.warning(f"Initiating emergency landing: {reason}")
        
        try:
            if self.controller and self.controller.is_flying:
                if self.controller.land():
                    self.logger.info("Emergency landing successful")
                    self._trigger_safety_event(
                        SafetyLevel.INFO,
                        "Emergency landing completed",
                        "landing_complete"
                    )
                else:
                    self.logger.error("Emergency landing failed")
                    # Try emergency stop as last resort
                    self.trigger_emergency_stop("Emergency landing failed")
            
        except Exception as e:
            self.logger.error(f"Emergency landing error: {e}")
            self.trigger_emergency_stop("Emergency landing error")
    
    def _trigger_safety_event(self, level: SafetyLevel, message: str, event_type: str):
        """
        Trigger safety event and notify callbacks
        
        Args:
            level: Safety level
            message: Event message
            event_type: Type of safety event
        """
        event = {
            'timestamp': time.time(),
            'level': level,
            'message': message,
            'type': event_type
        }
        
        self.safety_events.append(event)
        
        # Limit event history
        if len(self.safety_events) > 100:
            self.safety_events = self.safety_events[-50:]
        
        # Log the event
        log_method = {
            SafetyLevel.INFO: self.logger.info,
            SafetyLevel.WARNING: self.logger.warning,
            SafetyLevel.CRITICAL: self.logger.error,
            SafetyLevel.EMERGENCY: self.logger.critical
        }.get(level, self.logger.info)
        
        log_method(f"SAFETY {level.value.upper()}: {message}")
        
        # Notify callback
        if self.safety_alert_callback:
            try:
                self.safety_alert_callback(event)
            except Exception as e:
                self.logger.error(f"Safety callback error: {e}")
    
    def on_takeoff(self):
        """Called when drone takes off"""
        self.flight_start_time = time.time()
        self.emergency_stop_triggered = False
        self.auto_landing_triggered = False
        
        self._trigger_safety_event(
            SafetyLevel.INFO,
            "Flight started - safety monitoring active",
            "takeoff"
        )
    
    def on_landing(self):
        """Called when drone lands"""
        self.flight_start_time = None
        
        self._trigger_safety_event(
            SafetyLevel.INFO,
            "Flight ended - safety monitoring standby",
            "landing"
        )
    
    def on_telemetry_update(self, telemetry_data: Dict[str, Any]):
        """
        Called when telemetry data is received
        
        Args:
            telemetry_data: Parsed telemetry data
        """
        self.last_telemetry_time = time.time()
        
        # Update controller state from telemetry
        if self.controller and telemetry_data:
            if 'battery' in telemetry_data:
                self.controller.current_battery = telemetry_data['battery']
            
            if 'altitude' in telemetry_data:
                self.controller.current_altitude = telemetry_data['altitude']
    
    def on_heartbeat(self):
        """Called when heartbeat is received"""
        self.last_heartbeat_time = time.time()
    
    def set_safety_alert_callback(self, callback: Callable):
        """Set callback for safety alerts"""
        self.safety_alert_callback = callback
    
    def set_emergency_callback(self, callback: Callable):
        """Set callback for emergency events"""
        self.emergency_callback = callback
    
    def get_safety_status(self) -> Dict[str, Any]:
        """
        Get current safety status
        
        Returns:
            dict: Safety status information
        """
        return {
            'safety_enabled': self.safety_enabled,
            'monitoring_active': self.monitoring_active,
            'emergency_stop_triggered': self.emergency_stop_triggered,
            'auto_landing_triggered': self.auto_landing_triggered,
            'flight_time': time.time() - self.flight_start_time if self.flight_start_time else 0,
            'max_flight_time': self.max_flight_time,
            'battery_critical_threshold': self.critical_battery,
            'recent_events': self.safety_events[-10:] if self.safety_events else []
        }
    
    def enable_safety(self):
        """Enable safety monitoring"""
        self.safety_enabled = True
        self.logger.info("Safety monitoring enabled")
    
    def disable_safety(self):
        """Disable safety monitoring (use with caution!)"""
        self.safety_enabled = False
        self.logger.warning("Safety monitoring DISABLED - use with extreme caution!")
    
    def reset_safety_state(self):
        """Reset safety state (after landing)"""
        self.emergency_stop_triggered = False
        self.auto_landing_triggered = False
        self.flight_start_time = None
        
        self.logger.info("Safety state reset")