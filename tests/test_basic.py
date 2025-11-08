#!/usr/bin/env python3
"""
Basic test script for P8 Pro Drone Controller V4
Tests core functionality without requiring actual drone connection
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestDroneController(unittest.TestCase):
    """Test basic drone controller functionality"""
    
    def setUp(self):
        """Set up test environment"""
        from communication.wifi_connection import DroneConnection
        from control.drone_controller import DroneController
        
        # Create mock connection
        self.mock_connection = Mock()
        self.mock_connection.is_connected = True
        self.mock_connection.send_command.return_value = "ok"
        
        # Create controller with mock
        self.controller = DroneController(self.mock_connection)
    
    def test_controller_initialization(self):
        """Test controller initialization"""
        result = self.controller.initialize()
        self.assertTrue(result)
        self.mock_connection.send_command.assert_called()
    
    def test_movement_commands(self):
        """Test movement command validation"""
        # Valid movement
        result = self.controller.move_forward(100)
        self.assertFalse(result)  # Should fail because not flying
        
        # Invalid distance
        result = self.controller.move_forward(10)  # Too small
        self.assertFalse(result)
        
        result = self.controller.move_forward(600)  # Too large
        self.assertFalse(result)
    
    def test_speed_setting(self):
        """Test speed setting validation"""
        # Valid speed
        result = self.controller.set_speed(50)
        self.assertTrue(result)
        
        # Invalid speeds
        result = self.controller.set_speed(5)  # Too low
        self.assertFalse(result)
        
        result = self.controller.set_speed(150)  # Too high
        self.assertFalse(result)

class TestTelemetryParser(unittest.TestCase):
    """Test telemetry parsing functionality"""
    
    def setUp(self):
        """Set up test environment"""
        from utils.telemetry_parser import TelemetryParser
        self.parser = TelemetryParser()
    
    def test_battery_parsing(self):
        """Test battery level parsing"""
        telemetry = "bat:85 h:120 temp:32"
        parsed = self.parser.parse(telemetry)
        
        self.assertEqual(parsed['battery'], 85)
        self.assertEqual(parsed['altitude'], 120)
        self.assertEqual(parsed['temperature'], 32)
    
    def test_critical_alerts(self):
        """Test critical condition detection"""
        # Low battery
        parsed_data = {'battery': 8}
        alerts = self.parser.get_critical_alerts(parsed_data)
        self.assertTrue(any('CRITICAL BATTERY' in alert for alert in alerts))
        
        # High temperature
        parsed_data = {'temperature': 85}
        alerts = self.parser.get_critical_alerts(parsed_data)
        self.assertTrue(any('HIGH TEMPERATURE' in alert for alert in alerts))

class TestConfiguration(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test environment"""
        from config.settings import ConfigManager
        self.config = ConfigManager()
    
    def test_default_values(self):
        """Test default configuration values"""
        drone_ip = self.config.get('network.drone_ip')
        self.assertEqual(drone_ip, '192.168.1.1')
        
        max_altitude = self.config.get('flight.max_altitude')
        self.assertEqual(max_altitude, 500)
    
    def test_config_validation(self):
        """Test configuration validation"""
        errors = self.config.validate_config()
        self.assertEqual(len(errors), 0)  # Should have no errors with defaults

def run_basic_tests():
    """Run basic functionality tests"""
    print("P8 Pro Drone Controller V4 - Basic Tests")
    print("=" * 50)
    
    # Test imports
    try:
        print("Testing imports...")
        from communication.wifi_connection import DroneConnection
        from control.drone_controller import DroneController
        from utils.telemetry_parser import TelemetryParser
        from utils.safety_manager import SafetyManager
        from config.settings import ConfigManager
        print("✓ All modules imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test configuration
    try:
        print("\nTesting configuration...")
        config = ConfigManager()
        drone_ip = config.get('network.drone_ip', 'default')
        print(f"✓ Configuration loaded (drone IP: {drone_ip})")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False
    
    # Test telemetry parser
    try:
        print("\nTesting telemetry parser...")
        parser = TelemetryParser()
        test_data = "bat:75 h:150 vgx:10 temp:25"
        parsed = parser.parse(test_data)
        print(f"✓ Telemetry parsed (battery: {parsed.get('battery', 'N/A')}%)")
    except Exception as e:
        print(f"✗ Telemetry parser error: {e}")
        return False
    
    # Test mock connection
    try:
        print("\nTesting mock connection...")
        connection = DroneConnection("127.0.0.1", 8889, 8890)
        # Don't actually connect, just test object creation
        print("✓ Connection object created successfully")
    except Exception as e:
        print(f"✗ Connection creation error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All basic tests passed!")
    print("\nNext steps:")
    print("1. Connect your P8 Pro drone")
    print("2. Run: python main.py")
    print("3. Click 'Connect' in the application")
    
    return True

if __name__ == "__main__":
    # Run basic tests
    if len(sys.argv) > 1 and sys.argv[1] == "--unittest":
        # Run unittest suite
        unittest.main(argv=[''], exit=False, verbosity=2)
    else:
        # Run basic functionality tests
        success = run_basic_tests()
        sys.exit(0 if success else 1)