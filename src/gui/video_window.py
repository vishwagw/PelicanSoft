"""
Video Display Window for P8 Pro Drone Controller
Handles video stream display with HUD overlay and recording capabilities
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import logging
from typing import Optional, Dict, Any

from communication.video_stream import VideoStream, HUDOverlay

class VideoWindow:
    """Video display window with HUD overlay"""
    
    def __init__(self, parent, config: Dict[str, Any]):
        """
        Initialize video window
        
        Args:
            parent: Parent tkinter window
            config: Configuration dictionary
        """
        self.parent = parent
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Video components
        self.video_stream: Optional[VideoStream] = None
        self.hud_overlay = HUDOverlay()
        
        # GUI components
        self.video_window: Optional[tk.Toplevel] = None
        self.video_label: Optional[tk.Label] = None
        self.control_frame: Optional[tk.Frame] = None
        
        # Video state
        self.is_recording = False
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.recording_filename = ""
        
        # Display state
        self.display_width = 960
        self.display_height = 720
        self.auto_resize = True
        
        # Update thread
        self.display_thread: Optional[threading.Thread] = None
        self.display_active = False
        
        # Telemetry data for HUD
        self.latest_telemetry = {}
        self.latest_flight_status = {}
        
        # Video statistics
        self.frames_displayed = 0
        self.last_fps_update = time.time()
        self.display_fps = 0
        
    def create_video_window(self):
        """Create video display window"""
        if self.video_window is not None:
            self.video_window.lift()
            return
        
        # Create video window
        self.video_window = tk.Toplevel(self.parent)
        self.video_window.title("P8 Pro - Camera Feed")
        self.video_window.geometry(f"{self.display_width + 20}x{self.display_height + 100}")
        
        # Configure window
        self.video_window.protocol("WM_DELETE_WINDOW", self.close_video_window)
        self.video_window.resizable(True, True)
        
        # Create main frame
        main_frame = ttk.Frame(self.video_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video display area
        self.video_label = tk.Label(main_frame, bg='black', text="No Video Signal",
                                   fg='white', font=('Arial', 16))
        self.video_label.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Control panel
        self.create_video_controls(main_frame)
        
        # Initialize video stream
        drone_ip = self.config.get('network', {}).get('drone_ip', '192.168.1.1')
        video_port = self.config.get('network', {}).get('video_port', 11111)
        
        self.video_stream = VideoStream(drone_ip, video_port)
        self.video_stream.set_frame_callback(self.on_frame_received)
        self.video_stream.set_error_callback(self.on_video_error)
        
        self.logger.info("Video window created")
    
    def create_video_controls(self, parent):
        """Create video control panel"""
        self.control_frame = ttk.LabelFrame(parent, text="Video Controls", padding="5")
        self.control_frame.pack(fill=tk.X, pady=5)
        
        # First row - basic controls
        controls_row1 = ttk.Frame(self.control_frame)
        controls_row1.pack(fill=tk.X, pady=2)
        
        # Start/Stop video
        self.video_btn = ttk.Button(controls_row1, text="Start Video", 
                                   command=self.toggle_video_stream)
        self.video_btn.pack(side=tk.LEFT, padx=5)
        
        # Recording controls
        self.record_btn = ttk.Button(controls_row1, text="Start Recording", 
                                   command=self.toggle_recording, state='disabled')
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        # HUD toggle
        self.hud_btn = ttk.Button(controls_row1, text="Toggle HUD", 
                                 command=self.toggle_hud)
        self.hud_btn.pack(side=tk.LEFT, padx=5)
        
        # Snapshot
        self.snapshot_btn = ttk.Button(controls_row1, text="Snapshot", 
                                     command=self.take_snapshot, state='disabled')
        self.snapshot_btn.pack(side=tk.LEFT, padx=5)
        
        # Second row - HUD elements
        controls_row2 = ttk.Frame(self.control_frame)
        controls_row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(controls_row2, text="HUD Elements:").pack(side=tk.LEFT, padx=5)
        
        # HUD element toggles
        self.crosshair_var = tk.BooleanVar(value=True)
        crosshair_cb = ttk.Checkbutton(controls_row2, text="Crosshair", 
                                     variable=self.crosshair_var,
                                     command=lambda: self.hud_overlay.toggle_element('crosshair'))
        crosshair_cb.pack(side=tk.LEFT, padx=5)
        
        self.telemetry_var = tk.BooleanVar(value=True)
        telemetry_cb = ttk.Checkbutton(controls_row2, text="Telemetry", 
                                     variable=self.telemetry_var,
                                     command=lambda: self.hud_overlay.toggle_element('telemetry'))
        telemetry_cb.pack(side=tk.LEFT, padx=5)
        
        self.horizon_var = tk.BooleanVar(value=True)
        horizon_cb = ttk.Checkbutton(controls_row2, text="Horizon", 
                                   variable=self.horizon_var,
                                   command=lambda: self.hud_overlay.toggle_element('horizon'))
        horizon_cb.pack(side=tk.LEFT, padx=5)
        
        self.compass_var = tk.BooleanVar(value=True)
        compass_cb = ttk.Checkbutton(controls_row2, text="Compass", 
                                   variable=self.compass_var,
                                   command=lambda: self.hud_overlay.toggle_element('compass'))
        compass_cb.pack(side=tk.LEFT, padx=5)
        
        # Third row - status
        status_row = ttk.Frame(self.control_frame)
        status_row.pack(fill=tk.X, pady=2)
        
        # Status labels
        self.status_var = tk.StringVar(value="Video: Stopped")
        ttk.Label(status_row, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        self.fps_var = tk.StringVar(value="FPS: 0")
        ttk.Label(status_row, textvariable=self.fps_var).pack(side=tk.LEFT, padx=5)
        
        self.recording_var = tk.StringVar(value="")
        ttk.Label(status_row, textvariable=self.recording_var, 
                 foreground="red").pack(side=tk.LEFT, padx=5)
    
    def toggle_video_stream(self):
        """Toggle video stream on/off"""
        if not self.video_stream:
            return
        
        if self.video_stream.is_streaming:
            self.stop_video_stream()
        else:
            self.start_video_stream()
    
    def start_video_stream(self):
        """Start video stream"""
        if not self.video_stream:
            return
        
        try:
            if self.video_stream.start_stream():
                self.video_btn.config(text="Stop Video")
                self.record_btn.config(state='normal')
                self.snapshot_btn.config(state='normal')
                self.status_var.set("Video: Starting...")
                
                # Start display thread
                self.display_active = True
                self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
                self.display_thread.start()
                
                self.logger.info("Video stream started")
            else:
                self.status_var.set("Video: Failed to start")
                
        except Exception as e:
            self.logger.error(f"Error starting video stream: {e}")
            self.status_var.set(f"Video: Error - {e}")
    
    def stop_video_stream(self):
        """Stop video stream"""
        if not self.video_stream:
            return
        
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()
        
        # Stop display
        self.display_active = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2.0)
        
        # Stop stream
        self.video_stream.stop_stream()
        
        # Update GUI
        self.video_btn.config(text="Start Video")
        self.record_btn.config(state='disabled')
        self.snapshot_btn.config(state='disabled')
        self.status_var.set("Video: Stopped")
        self.fps_var.set("FPS: 0")
        
        # Clear video display
        if self.video_label:
            self.video_label.config(image='', text="No Video Signal")
        
        self.logger.info("Video stream stopped")
    
    def _display_loop(self):
        """Main display loop for video frames"""
        while self.display_active:
            try:
                if self.video_stream and self.video_stream.is_streaming:
                    frame = self.video_stream.get_latest_frame()
                    
                    if frame is not None:
                        # Apply HUD overlay
                        hud_frame = self.hud_overlay.apply_hud(frame, 
                                                             self.latest_telemetry,
                                                             self.latest_flight_status)
                        
                        # Update display
                        self.update_video_display(hud_frame)
                        
                        # Record if active
                        if self.is_recording and self.video_writer:
                            self.video_writer.write(hud_frame)
                        
                        # Update statistics
                        self.frames_displayed += 1
                        current_time = time.time()
                        if current_time - self.last_fps_update >= 1.0:
                            self.display_fps = self.frames_displayed / (current_time - self.last_fps_update)
                            self.frames_displayed = 0
                            self.last_fps_update = current_time
                            
                            # Update GUI
                            self.video_window.after(0, self._update_status)
                
                time.sleep(1/30)  # Target 30 FPS display
                
            except Exception as e:
                self.logger.error(f"Display loop error: {e}")
                time.sleep(0.1)
    
    def update_video_display(self, frame: np.ndarray):
        """Update video display with new frame"""
        if not self.video_label or not self.video_window:
            return
        
        try:
            # Resize frame for display
            display_frame = self._resize_frame_for_display(frame)
            
            # Convert to PIL Image
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update display in main thread
            self.video_window.after(0, self._update_display_image, photo)
            
        except Exception as e:
            self.logger.error(f"Display update error: {e}")
    
    def _update_display_image(self, photo):
        """Update display image in main thread"""
        if self.video_label:
            self.video_label.config(image=photo, text="")
            self.video_label.image = photo  # Keep reference
    
    def _update_status(self):
        """Update status display"""
        if self.video_stream:
            stats = self.video_stream.get_stream_stats()
            self.status_var.set(f"Video: {'Active' if stats['is_streaming'] else 'Stopped'}")
            self.fps_var.set(f"FPS: {self.display_fps:.1f}")
    
    def _resize_frame_for_display(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame for display window"""
        if not self.auto_resize:
            return frame
        
        current_height, current_width = frame.shape[:2]
        
        # Calculate scale to fit display
        scale_w = self.display_width / current_width
        scale_h = self.display_height / current_height
        scale = min(scale_w, scale_h)
        
        # Resize if needed
        if scale != 1.0:
            new_width = int(current_width * scale)
            new_height = int(current_height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        return frame
    
    def toggle_recording(self):
        """Toggle video recording"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start video recording"""
        if not self.video_stream or not self.video_stream.is_streaming:
            messagebox.showwarning("Recording", "Start video stream first")
            return
        
        # Get save filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_filename = f"flight_recording_{timestamp}.mp4"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("AVI files", "*.avi")],
            initialname=default_filename
        )
        
        if not filename:
            return
        
        try:
            # Get frame dimensions
            frame = self.video_stream.get_latest_frame()
            if frame is None:
                messagebox.showerror("Recording", "No video frame available")
                return
            
            height, width = frame.shape[:2]
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
            
            if not self.video_writer.isOpened():
                raise Exception("Failed to open video writer")
            
            self.is_recording = True
            self.recording_filename = filename
            
            # Update GUI
            self.record_btn.config(text="Stop Recording")
            self.recording_var.set("● REC")
            
            self.logger.info(f"Recording started: {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            messagebox.showerror("Recording", f"Failed to start recording: {e}")
    
    def stop_recording(self):
        """Stop video recording"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        # Update GUI
        self.record_btn.config(text="Start Recording")
        self.recording_var.set("")
        
        self.logger.info(f"Recording stopped: {self.recording_filename}")
        messagebox.showinfo("Recording", f"Recording saved: {self.recording_filename}")
    
    def take_snapshot(self):
        """Take a snapshot of current frame"""
        if not self.video_stream or not self.video_stream.is_streaming:
            messagebox.showwarning("Snapshot", "Start video stream first")
            return
        
        frame = self.video_stream.get_latest_frame()
        if frame is None:
            messagebox.showwarning("Snapshot", "No video frame available")
            return
        
        # Apply HUD overlay
        hud_frame = self.hud_overlay.apply_hud(frame, self.latest_telemetry,
                                             self.latest_flight_status)
        
        # Get save filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_filename = f"snapshot_{timestamp}.jpg"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png")],
            initialname=default_filename
        )
        
        if filename:
            cv2.imwrite(filename, hud_frame)
            self.logger.info(f"Snapshot saved: {filename}")
            messagebox.showinfo("Snapshot", f"Snapshot saved: {filename}")
    
    def toggle_hud(self):
        """Toggle HUD overlay"""
        self.hud_overlay.toggle_hud()
        state = "enabled" if self.hud_overlay.hud_enabled else "disabled"
        self.logger.info(f"HUD {state}")
    
    def on_frame_received(self, frame: np.ndarray):
        """Callback for new video frames"""
        # This callback is called from video stream thread
        # Frame processing is handled in display loop
        pass
    
    def on_video_error(self, error: Exception):
        """Callback for video stream errors"""
        self.logger.error(f"Video stream error: {error}")
        if self.video_window:
            self.video_window.after(0, lambda: self.status_var.set(f"Video Error: {error}"))
    
    def update_telemetry(self, telemetry_data: Dict[str, Any]):
        """Update telemetry data for HUD"""
        self.latest_telemetry = telemetry_data.copy()
    
    def update_flight_status(self, flight_status: Dict[str, Any]):
        """Update flight status for HUD"""
        self.latest_flight_status = flight_status.copy()
    
    def close_video_window(self):
        """Close video window"""
        # Stop video stream
        self.stop_video_stream()
        
        # Destroy window
        if self.video_window:
            self.video_window.destroy()
            self.video_window = None
        
        self.logger.info("Video window closed")
    
    def is_window_open(self) -> bool:
        """Check if video window is open"""
        return self.video_window is not None and self.video_window.winfo_exists()