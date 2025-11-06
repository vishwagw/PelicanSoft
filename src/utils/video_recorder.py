"""
Video Recording Module for P8 Pro Drone Controller
Handles video recording with telemetry overlay and metadata
"""

import cv2
import numpy as np
import json
import time
import threading
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

class VideoRecorder:
    """Records video with telemetry data overlay"""
    
    def __init__(self, output_dir: str = "recordings"):
        """
        Initialize video recorder
        
        Args:
            output_dir: Directory to save recordings
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Recording state
        self.is_recording = False
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.recording_filename = ""
        self.metadata_filename = ""
        
        # Recording settings
        self.fps = 30.0
        self.codec = cv2.VideoWriter_fourcc(*'mp4v')
        self.resolution = (960, 720)
        
        # Telemetry data storage
        self.telemetry_log: List[Dict[str, Any]] = []
        self.recording_start_time = 0
        
        # Statistics
        self.frames_recorded = 0
        self.recording_duration = 0
    
    def start_recording(self, filename: Optional[str] = None, 
                       resolution: Optional[tuple] = None) -> bool:
        """
        Start video recording
        
        Args:
            filename: Output filename (auto-generated if None)
            resolution: Video resolution (uses default if None)
            
        Returns:
            bool: True if recording started successfully
        """
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return False
        
        try:
            # Generate filename if not provided
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"flight_recording_{timestamp}.mp4"
            
            # Ensure proper extension
            if not filename.endswith(('.mp4', '.avi', '.mov')):
                filename += '.mp4'
            
            self.recording_filename = str(self.output_dir / filename)
            
            # Set resolution
            if resolution:
                self.resolution = resolution
            
            # Initialize video writer
            self.video_writer = cv2.VideoWriter(
                self.recording_filename,
                self.codec,
                self.fps,
                self.resolution
            )
            
            if not self.video_writer.isOpened():
                raise Exception("Failed to initialize video writer")
            
            # Initialize metadata file
            metadata_filename = self.recording_filename.replace('.mp4', '_metadata.json')
            self.metadata_filename = metadata_filename
            
            # Reset recording state
            self.is_recording = True
            self.recording_start_time = time.time()
            self.frames_recorded = 0
            self.telemetry_log = []
            
            # Save initial metadata
            self._save_recording_metadata()
            
            self.logger.info(f"Recording started: {self.recording_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self._cleanup_recording()
            return False
    
    def stop_recording(self) -> bool:
        """
        Stop video recording
        
        Returns:
            bool: True if recording stopped successfully
        """
        if not self.is_recording:
            self.logger.warning("No recording in progress")
            return False
        
        try:
            self.is_recording = False
            self.recording_duration = time.time() - self.recording_start_time
            
            # Release video writer
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            # Save final metadata
            self._save_recording_metadata()
            
            self.logger.info(f"Recording stopped: {self.recording_filename}")
            self.logger.info(f"Duration: {self.recording_duration:.1f}s, Frames: {self.frames_recorded}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
            return False
        finally:
            self._cleanup_recording()
    
    def record_frame(self, frame: np.ndarray, telemetry_data: Optional[Dict[str, Any]] = None,
                    flight_status: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record a single frame with telemetry data
        
        Args:
            frame: Video frame to record
            telemetry_data: Current telemetry data
            flight_status: Current flight status
            
        Returns:
            bool: True if frame recorded successfully
        """
        if not self.is_recording or not self.video_writer:
            return False
        
        try:
            # Resize frame if needed
            if frame.shape[:2][::-1] != self.resolution:
                frame = cv2.resize(frame, self.resolution)
            
            # Write frame
            self.video_writer.write(frame)
            self.frames_recorded += 1
            
            # Log telemetry data
            if telemetry_data or flight_status:
                self._log_telemetry(telemetry_data, flight_status)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording frame: {e}")
            return False
    
    def _log_telemetry(self, telemetry_data: Optional[Dict[str, Any]], 
                      flight_status: Optional[Dict[str, Any]]):
        """Log telemetry data with timestamp"""
        timestamp = time.time() - self.recording_start_time
        
        telemetry_entry = {
            'timestamp': timestamp,
            'frame_number': self.frames_recorded
        }
        
        if telemetry_data:
            telemetry_entry['telemetry'] = telemetry_data.copy()
        
        if flight_status:
            telemetry_entry['flight_status'] = flight_status.copy()
        
        self.telemetry_log.append(telemetry_entry)
        
        # Limit telemetry log size (keep last 1000 entries)
        if len(self.telemetry_log) > 1000:
            self.telemetry_log = self.telemetry_log[-500:]
    
    def _save_recording_metadata(self):
        """Save recording metadata to JSON file"""
        try:
            metadata = {
                'recording_info': {
                    'filename': Path(self.recording_filename).name,
                    'start_time': time.strftime("%Y-%m-%d %H:%M:%S", 
                                               time.localtime(self.recording_start_time)),
                    'duration': self.recording_duration,
                    'frames_recorded': self.frames_recorded,
                    'fps': self.fps,
                    'resolution': self.resolution,
                    'codec': 'mp4v'
                },
                'telemetry_data': self.telemetry_log
            }
            
            with open(self.metadata_filename, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")
    
    def _cleanup_recording(self):
        """Cleanup recording resources"""
        self.is_recording = False
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
    
    def get_recording_stats(self) -> Dict[str, Any]:
        """
        Get current recording statistics
        
        Returns:
            dict: Recording statistics
        """
        duration = time.time() - self.recording_start_time if self.is_recording else self.recording_duration
        
        return {
            'is_recording': self.is_recording,
            'filename': Path(self.recording_filename).name if self.recording_filename else "",
            'duration': duration,
            'frames_recorded': self.frames_recorded,
            'fps': self.fps,
            'resolution': self.resolution,
            'telemetry_entries': len(self.telemetry_log)
        }


class TelemetryVideoAnalyzer:
    """Analyzes recorded video with telemetry data"""
    
    def __init__(self, video_file: str, metadata_file: str):
        """
        Initialize analyzer
        
        Args:
            video_file: Path to video file
            metadata_file: Path to metadata JSON file
        """
        self.video_file = video_file
        self.metadata_file = metadata_file
        self.logger = logging.getLogger(__name__)
        
        self.metadata = None
        self.telemetry_data = []
        
        self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from JSON file"""
        try:
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
            
            self.telemetry_data = self.metadata.get('telemetry_data', [])
            self.logger.info(f"Loaded metadata with {len(self.telemetry_data)} telemetry entries")
            
        except Exception as e:
            self.logger.error(f"Error loading metadata: {e}")
    
    def get_telemetry_at_time(self, timestamp: float) -> Optional[Dict[str, Any]]:
        """
        Get telemetry data at specific timestamp
        
        Args:
            timestamp: Time in seconds from start of recording
            
        Returns:
            dict: Telemetry data or None if not found
        """
        if not self.telemetry_data:
            return None
        
        # Find closest telemetry entry
        closest_entry = min(self.telemetry_data, 
                          key=lambda x: abs(x.get('timestamp', 0) - timestamp))
        
        return closest_entry
    
    def get_flight_summary(self) -> Dict[str, Any]:
        """
        Generate flight summary from telemetry data
        
        Returns:
            dict: Flight summary statistics
        """
        if not self.telemetry_data:
            return {}
        
        # Extract data points
        batteries = []
        altitudes = []
        speeds = []
        temperatures = []
        
        for entry in self.telemetry_data:
            telemetry = entry.get('telemetry', {})
            
            if 'battery' in telemetry:
                batteries.append(telemetry['battery'])
            if 'altitude' in telemetry:
                altitudes.append(telemetry['altitude'])
            if 'speed_total' in telemetry:
                speeds.append(telemetry['speed_total'])
            if 'temperature' in telemetry:
                temperatures.append(telemetry['temperature'])
        
        summary = {
            'recording_info': self.metadata.get('recording_info', {}),
            'flight_stats': {
                'battery': {
                    'start': batteries[0] if batteries else 0,
                    'end': batteries[-1] if batteries else 0,
                    'min': min(batteries) if batteries else 0,
                    'average': sum(batteries) / len(batteries) if batteries else 0
                },
                'altitude': {
                    'max': max(altitudes) if altitudes else 0,
                    'average': sum(altitudes) / len(altitudes) if altitudes else 0,
                    'min': min(altitudes) if altitudes else 0
                },
                'speed': {
                    'max': max(speeds) if speeds else 0,
                    'average': sum(speeds) / len(speeds) if speeds else 0
                },
                'temperature': {
                    'max': max(temperatures) if temperatures else 0,
                    'min': min(temperatures) if temperatures else 0,
                    'average': sum(temperatures) / len(temperatures) if temperatures else 0
                }
            }
        }
        
        return summary
    
    def export_telemetry_csv(self, output_file: str):
        """
        Export telemetry data to CSV file
        
        Args:
            output_file: Output CSV filename
        """
        try:
            import csv
            
            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'frame_number', 'battery', 'altitude', 
                            'speed_total', 'temperature', 'pitch', 'roll', 'yaw']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for entry in self.telemetry_data:
                    telemetry = entry.get('telemetry', {})
                    
                    row = {
                        'timestamp': entry.get('timestamp', 0),
                        'frame_number': entry.get('frame_number', 0),
                        'battery': telemetry.get('battery', ''),
                        'altitude': telemetry.get('altitude', ''),
                        'speed_total': telemetry.get('speed_total', ''),
                        'temperature': telemetry.get('temperature', ''),
                        'pitch': telemetry.get('pitch', ''),
                        'roll': telemetry.get('roll', ''),
                        'yaw': telemetry.get('yaw', '')
                    }
                    
                    writer.writerow(row)
            
            self.logger.info(f"Telemetry data exported to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error exporting telemetry CSV: {e}")


def create_flight_report(video_file: str, metadata_file: str, output_file: str):
    """
    Create HTML flight report with telemetry analysis
    
    Args:
        video_file: Path to video file
        metadata_file: Path to metadata JSON file
        output_file: Output HTML filename
    """
    try:
        analyzer = TelemetryVideoAnalyzer(video_file, metadata_file)
        summary = analyzer.get_flight_summary()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flight Report - {Path(video_file).name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; text-align: center; }}
                .video-container {{ text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Flight Report</h1>
                <p><strong>Video:</strong> {Path(video_file).name}</p>
                <p><strong>Date:</strong> {summary.get('recording_info', {}).get('start_time', 'Unknown')}</p>
                <p><strong>Duration:</strong> {summary.get('recording_info', {}).get('duration', 0):.1f} seconds</p>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>Battery</h3>
                    <p>Start: {summary.get('flight_stats', {}).get('battery', {}).get('start', 0)}%</p>
                    <p>End: {summary.get('flight_stats', {}).get('battery', {}).get('end', 0)}%</p>
                    <p>Min: {summary.get('flight_stats', {}).get('battery', {}).get('min', 0)}%</p>
                </div>
                
                <div class="stat-box">
                    <h3>Altitude</h3>
                    <p>Max: {summary.get('flight_stats', {}).get('altitude', {}).get('max', 0)} cm</p>
                    <p>Avg: {summary.get('flight_stats', {}).get('altitude', {}).get('average', 0):.1f} cm</p>
                </div>
                
                <div class="stat-box">
                    <h3>Speed</h3>
                    <p>Max: {summary.get('flight_stats', {}).get('speed', {}).get('max', 0):.1f} cm/s</p>
                    <p>Avg: {summary.get('flight_stats', {}).get('speed', {}).get('average', 0):.1f} cm/s</p>
                </div>
            </div>
            
            <div class="video-container">
                <video width="800" controls>
                    <source src="{Path(video_file).name}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logging.info(f"Flight report created: {output_file}")
        
    except Exception as e:
        logging.error(f"Error creating flight report: {e}")