#!/usr/bin/env python3
"""
Video System Test for P8 Pro Drone Controller V4
Tests video streaming, HUD overlay, and recording functionality
"""

import sys
import os
import time
import cv2
import numpy as np

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_video_components():
    """Test video system components"""
    print("P8 Pro Drone Controller V4 - Video System Test")
    print("=" * 55)
    
    # Test video imports
    try:
        print("Testing video imports...")
        from communication.video_stream import VideoStream, HUDOverlay
        from utils.video_recorder import VideoRecorder, TelemetryVideoAnalyzer
        from gui.video_window import VideoWindow
        print("✓ Video modules imported successfully")
    except ImportError as e:
        print(f"✗ Video import error: {e}")
        return False
    
    # Test HUD overlay
    try:
        print("\nTesting HUD overlay...")
        hud = HUDOverlay()
        
        # Create test frame
        test_frame = np.zeros((720, 960, 3), dtype=np.uint8)
        test_telemetry = {
            'battery': 75,
            'altitude': 150,
            'speed_total': 25.5,
            'pitch': 5,
            'roll': -2,
            'yaw': 180,
            'temperature': 35
        }
        test_flight_status = {
            'is_flying': True,
            'mode': 'manual',
            'flight_time': 120
        }
        
        # Apply HUD
        hud_frame = hud.apply_hud(test_frame, test_telemetry, test_flight_status)
        
        if hud_frame is not None and hud_frame.shape == test_frame.shape:
            print("✓ HUD overlay working correctly")
        else:
            print("✗ HUD overlay failed")
            return False
            
    except Exception as e:
        print(f"✗ HUD overlay error: {e}")
        return False
    
    # Test video recorder
    try:
        print("\nTesting video recorder...")
        recorder = VideoRecorder("test_recordings")
        
        # Test recorder creation
        stats = recorder.get_recording_stats()
        if not stats['is_recording']:
            print("✓ Video recorder created successfully")
        else:
            print("✗ Video recorder in unexpected state")
            return False
            
    except Exception as e:
        print(f"✗ Video recorder error: {e}")
        return False
    
    # Test mock video stream
    try:
        print("\nTesting video stream (mock)...")
        video_stream = VideoStream("127.0.0.1", 11111)  # Mock IP
        
        # Don't actually try to connect, just test object creation
        stats = video_stream.get_stream_stats()
        if not stats['is_streaming']:
            print("✓ Video stream object created successfully")
        else:
            print("✗ Video stream in unexpected state")
            return False
            
    except Exception as e:
        print(f"✗ Video stream error: {e}")
        return False
    
    # Test OpenCV functionality
    try:
        print("\nTesting OpenCV functionality...")
        
        # Create test video frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Test basic OpenCV operations
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(frame, (320, 240))
        
        # Test text overlay
        cv2.putText(frame, "TEST", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        print("✓ OpenCV functionality working")
        
    except Exception as e:
        print(f"✗ OpenCV error: {e}")
        return False
    
    print("\n" + "=" * 55)
    print("✓ All video system tests passed!")
    print("\nVideo System Features Available:")
    print("• Real-time video streaming from P8 Pro camera")
    print("• HUD overlay with flight telemetry")
    print("• Video recording with metadata")
    print("• Customizable HUD elements")
    print("• Video analysis and reporting")
    print("\nTo use video features:")
    print("1. Connect to your P8 Pro drone")
    print("2. Run: python main.py")
    print("3. Click 'Open Camera' to start video window")
    print("4. Use video controls to start stream and recording")
    
    return True


def create_test_video():
    """Create a test video file for demonstration"""
    try:
        print("\nCreating test video demonstration...")
        
        # Create test video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('test_video_demo.mp4', fourcc, 20.0, (640, 480))
        
        # Create frames with moving elements
        for i in range(100):  # 5 seconds at 20 FPS
            # Create frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add moving circle (simulated drone movement)
            center_x = int(320 + 100 * np.sin(i * 0.1))
            center_y = int(240 + 50 * np.cos(i * 0.1))
            cv2.circle(frame, (center_x, center_y), 20, (0, 255, 0), -1)
            
            # Add simulated HUD elements
            cv2.putText(frame, f"BAT: {100 - i//2}%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"ALT: {50 + i}cm", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"SPD: {i % 50}cm/s", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add crosshair
            cv2.line(frame, (320-20, 240), (320+20, 240), (0, 255, 0), 2)
            cv2.line(frame, (320, 240-20), (320, 240+20), (0, 255, 0), 2)
            
            # Add frame counter
            cv2.putText(frame, f"Frame: {i}", (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            out.write(frame)
        
        out.release()
        print("✓ Test video created: test_video_demo.mp4")
        
    except Exception as e:
        print(f"✗ Error creating test video: {e}")


if __name__ == "__main__":
    # Run video system tests
    success = test_video_components()
    
    if success and len(sys.argv) > 1 and sys.argv[1] == "--create-demo":
        create_test_video()
    
    sys.exit(0 if success else 1)