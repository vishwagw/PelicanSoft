"""
Main GUI Window for P8 Pro Drone Controller
Provides user interface for drone control and monitoring
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import logging
from typing import Optional, Dict, Any

from communication.wifi_connection import DroneConnection
from control.drone_controller import DroneController, FlightMode
from utils.telemetry_parser import TelemetryParser
from gui.video_window import VideoWindow

class DroneControllerGUI:
    """Main application window for drone control"""
    
    def __init__(self, config: dict):
        """
        Initialize GUI application
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.connection: Optional[DroneConnection] = None
        self.controller: Optional[DroneController] = None
        self.telemetry_parser = TelemetryParser()
        self.video_window: Optional[VideoWindow] = None
        
        # GUI components
        self.root: Optional[tk.Tk] = None
        self.status_vars = {}
        self.control_buttons = {}
        self.video_status_var: Optional[tk.StringVar] = None
        
        # Status tracking
        self.is_connected = False
        self.last_telemetry_update = 0
        
        # Initialize GUI
        self.setup_gui()
    
    def setup_gui(self):
        """Initialize the main GUI window"""
        self.root = tk.Tk()
        self.root.title("Pelican Soft UAV controlling ground station")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Set window icon (if available)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Create GUI sections
        self.create_connection_section(main_frame)
        self.create_status_section(main_frame)
        self.create_control_section(main_frame)
        self.create_telemetry_section(main_frame)
        self.create_log_section(main_frame)
        
        # Setup key bindings
        self.setup_key_bindings()
        
        # Initialize connection
        self.initialize_connection()
        
        # Start GUI update loop
        self.update_gui()
    
    def create_connection_section(self, parent):
        """Create connection control section"""
        # Connection frame
        conn_frame = ttk.LabelFrame(parent, text="Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Connection settings
        ttk.Label(conn_frame, text="Drone IP:").grid(row=0, column=0, padx=5)
        self.ip_var = tk.StringVar(value=self.config.get('drone_ip', '192.168.1.1'))
        ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=15)
        ip_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=5)
        self.port_var = tk.StringVar(value=str(self.config.get('command_port', 8889)))
        port_entry = ttk.Entry(conn_frame, textvariable=self.port_var, width=8)
        port_entry.grid(row=0, column=3, padx=5)
        
        # Connection buttons
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_drone)
        self.connect_btn.grid(row=0, column=4, padx=10)
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", 
                                       command=self.disconnect_drone, state='disabled')
        self.disconnect_btn.grid(row=0, column=5, padx=5)
        
        # Video window button
        self.video_btn = ttk.Button(conn_frame, text="Open Camera", 
                                   command=self.toggle_video_window)
        self.video_btn.grid(row=0, column=6, padx=5)
        
        # Start Video button
        self.start_video_btn = ttk.Button(conn_frame, text="Start Video", 
                                         command=self.start_video_with_hud)
        self.start_video_btn.grid(row=0, column=7, padx=5)
        
        # Video status indicator
        self.video_status_var = tk.StringVar(value="Video: Stopped")
        video_status_label = ttk.Label(conn_frame, textvariable=self.video_status_var, 
                                     foreground="blue")
        video_status_label.grid(row=1, column=6, columnspan=2, padx=5, pady=2)
        
        # Connection status
        self.connection_status_var = tk.StringVar(value="Disconnected")
        status_label = ttk.Label(conn_frame, textvariable=self.connection_status_var, 
                               foreground="red")
        status_label.grid(row=0, column=8, padx=10)
    
    def create_status_section(self, parent):
        """Create drone status display section"""
        status_frame = ttk.LabelFrame(parent, text="Drone Status", padding="5")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), pady=5)
        
        # Status variables
        self.status_vars = {
            'battery': tk.StringVar(value="--"),
            'altitude': tk.StringVar(value="--"),
            'speed': tk.StringVar(value="--"),
            'mode': tk.StringVar(value="--"),
            'flying': tk.StringVar(value="No")
        }
        
        # Status display
        row = 0
        for label, var in self.status_vars.items():
            ttk.Label(status_frame, text=f"{label.title()}:").grid(row=row, column=0, 
                                                                 sticky=tk.W, padx=5)
            ttk.Label(status_frame, textvariable=var, width=10).grid(row=row, column=1, 
                                                                   sticky=tk.W, padx=5)
            row += 1
        
        # Emergency stop button
        self.emergency_btn = ttk.Button(status_frame, text="EMERGENCY STOP", 
                                      command=self.emergency_stop,
                                      style='Emergency.TButton')
        self.emergency_btn.grid(row=0, column=2, rowspan=2, padx=20, pady=5)
        
        # Configure emergency button style
        style = ttk.Style()
        style.configure('Emergency.TButton', foreground='white', background='red')
    
    def create_control_section(self, parent):
        """Create flight control section"""
        control_frame = ttk.LabelFrame(parent, text="Flight Controls", padding="10")
        control_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), pady=5, padx=(10, 0))
        
        # Basic flight controls
        flight_frame = ttk.Frame(control_frame)
        flight_frame.grid(row=0, column=0, columnspan=3, pady=10)
        
        self.control_buttons['takeoff'] = ttk.Button(flight_frame, text="Takeoff", 
                                                   command=self.takeoff_drone, state='disabled')
        self.control_buttons['takeoff'].grid(row=0, column=0, padx=5)
        
        self.control_buttons['land'] = ttk.Button(flight_frame, text="Land", 
                                                command=self.land_drone, state='disabled')
        self.control_buttons['land'].grid(row=0, column=1, padx=5)
        
        # Movement controls
        move_frame = ttk.LabelFrame(control_frame, text="Movement", padding="5")
        move_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        # Directional buttons
        self.control_buttons['forward'] = ttk.Button(move_frame, text="↑", 
                                                   command=lambda: self.move_drone('forward'),
                                                   state='disabled', width=3)
        self.control_buttons['forward'].grid(row=0, column=1)
        
        self.control_buttons['left'] = ttk.Button(move_frame, text="←", 
                                                command=lambda: self.move_drone('left'),
                                                state='disabled', width=3)
        self.control_buttons['left'].grid(row=1, column=0)
        
        self.control_buttons['right'] = ttk.Button(move_frame, text="→", 
                                                 command=lambda: self.move_drone('right'),
                                                 state='disabled', width=3)
        self.control_buttons['right'].grid(row=1, column=2)
        
        self.control_buttons['backward'] = ttk.Button(move_frame, text="↓", 
                                                    command=lambda: self.move_drone('backward'),
                                                    state='disabled', width=3)
        self.control_buttons['backward'].grid(row=2, column=1)
        
        # Vertical controls
        vert_frame = ttk.Frame(move_frame)
        vert_frame.grid(row=0, column=3, rowspan=3, padx=20)
        
        self.control_buttons['up'] = ttk.Button(vert_frame, text="Up", 
                                              command=lambda: self.move_drone('up'),
                                              state='disabled', width=5)
        self.control_buttons['up'].grid(row=0, column=0, pady=2)
        
        self.control_buttons['down'] = ttk.Button(vert_frame, text="Down", 
                                                command=lambda: self.move_drone('down'),
                                                state='disabled', width=5)
        self.control_buttons['down'].grid(row=1, column=0, pady=2)
        
        # Rotation controls
        rot_frame = ttk.Frame(move_frame)
        rot_frame.grid(row=1, column=1, padx=10)
        
        self.control_buttons['rotate_left'] = ttk.Button(rot_frame, text="↺", 
                                                       command=lambda: self.rotate_drone('left'),
                                                       state='disabled', width=3)
        self.control_buttons['rotate_left'].grid(row=0, column=0, padx=2)
        
        self.control_buttons['rotate_right'] = ttk.Button(rot_frame, text="↻", 
                                                        command=lambda: self.rotate_drone('right'),
                                                        state='disabled', width=3)
        self.control_buttons['rotate_right'].grid(row=0, column=1, padx=2)
        
        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Label(speed_frame, text="Speed:").grid(row=0, column=0)
        self.speed_var = tk.IntVar(value=50)
        speed_scale = ttk.Scale(speed_frame, from_=10, to=100, variable=self.speed_var,
                              orient=tk.HORIZONTAL, length=200, command=self.update_speed)
        speed_scale.grid(row=0, column=1, padx=10)
        
        self.speed_label = ttk.Label(speed_frame, text="50")
        self.speed_label.grid(row=0, column=2)
    
    def create_telemetry_section(self, parent):
        """Create telemetry display section"""
        telemetry_frame = ttk.LabelFrame(parent, text="Telemetry", padding="5")
        telemetry_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Telemetry text area
        self.telemetry_text = scrolledtext.ScrolledText(telemetry_frame, height=8, width=80)
        self.telemetry_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        telemetry_frame.columnconfigure(0, weight=1)
        telemetry_frame.rowconfigure(0, weight=1)
    
    def create_log_section(self, parent):
        """Create log display section"""
        log_frame = ttk.LabelFrame(parent, text="Log", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def setup_key_bindings(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<KeyPress-w>', lambda e: self.move_drone('forward') if self.is_connected else None)
        self.root.bind('<KeyPress-s>', lambda e: self.move_drone('backward') if self.is_connected else None)
        self.root.bind('<KeyPress-a>', lambda e: self.move_drone('left') if self.is_connected else None)
        self.root.bind('<KeyPress-d>', lambda e: self.move_drone('right') if self.is_connected else None)
        self.root.bind('<KeyPress-q>', lambda e: self.rotate_drone('left') if self.is_connected else None)
        self.root.bind('<KeyPress-e>', lambda e: self.rotate_drone('right') if self.is_connected else None)
        self.root.bind('<KeyPress-r>', lambda e: self.move_drone('up') if self.is_connected else None)
        self.root.bind('<KeyPress-f>', lambda e: self.move_drone('down') if self.is_connected else None)
        self.root.bind('<KeyPress-t>', lambda e: self.takeoff_drone() if self.is_connected else None)
        self.root.bind('<KeyPress-l>', lambda e: self.land_drone() if self.is_connected else None)
        self.root.bind('<KeyPress-space>', lambda e: self.emergency_stop())
        
        # Focus window to receive key events
        self.root.focus_set()
    
    def initialize_connection(self):
        """Initialize drone connection object"""
        drone_ip = self.config.get('drone_ip', '192.168.1.1')
        command_port = self.config.get('command_port', 8889)
        state_port = self.config.get('state_port', 8890)
        
        self.connection = DroneConnection(drone_ip, command_port, state_port)
        self.connection.set_telemetry_callback(self.on_telemetry_received)
        self.connection.set_connection_callback(self.on_connection_changed)
        
        self.controller = DroneController(self.connection)
    
    def toggle_video_window(self):
        """Toggle video window open/closed"""
        if self.video_window is None or not self.video_window.is_window_open():
            self.open_video_window()
        else:
            self.video_window.close_video_window()
            self.video_window = None
    
    def open_video_window(self):
        """Open video window"""
        try:
            self.video_window = VideoWindow(self.root, self.config)
            self.video_window.create_video_window()
            self.log_message("Video window opened")
        except Exception as e:
            self.log_message(f"Failed to open video window: {e}")
            self.logger.error(f"Video window error: {e}")
    
    def start_video_with_hud(self):
        """Start video streaming with HUD overlay"""
        try:
            # Open video window if not already open
            if self.video_window is None or not self.video_window.is_window_open():
                self.open_video_window()
            
            # Wait a moment for window to initialize
            if self.video_window:
                # Start video stream automatically
                self.root.after(500, self._auto_start_video)
                self.log_message("Starting video with HUD...")
            
        except Exception as e:
            self.log_message(f"Failed to start video: {e}")
            self.logger.error(f"Video start error: {e}")
    
    def _auto_start_video(self):
        """Automatically start video stream in video window"""
        if self.video_window and self.video_window.is_window_open():
            try:
                self.video_window.start_video_stream()
                self.video_status_var.set("Video: Starting...")
                # Update status after a delay
                self.root.after(2000, self._update_video_status)
            except Exception as e:
                self.log_message(f"Auto-start video failed: {e}")
                self.logger.error(f"Auto-start error: {e}")
                self.video_status_var.set("Video: Failed")
    
    def _update_video_status(self):
        """Update video status indicator"""
        if self.video_window and self.video_window.is_window_open():
            if hasattr(self.video_window.video_stream, 'is_streaming') and self.video_window.video_stream.is_streaming:
                self.video_status_var.set("Video: Active with HUD")
            else:
                self.video_status_var.set("Video: Stopped")
        else:
            self.video_status_var.set("Video: Stopped")
    
    def connect_drone(self):
        """Connect to drone"""
        def connect_thread():
            try:
                # Update connection parameters
                self.connection.drone_ip = self.ip_var.get()
                self.connection.command_port = int(self.port_var.get())
                
                self.log_message("Connecting to drone...")
                
                if self.connection.connect():
                    if self.controller.initialize():
                        self.log_message("Connected and initialized successfully")
                    else:
                        self.log_message("Connected but initialization failed")
                else:
                    self.log_message("Failed to connect to drone")
                    
            except Exception as e:
                self.log_message(f"Connection error: {e}")
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def disconnect_drone(self):
        """Disconnect from drone"""
        if self.connection:
            self.connection.disconnect()
        self.log_message("Disconnected from drone")
    
    def on_connection_changed(self, connected: bool):
        """Handle connection status change"""
        self.is_connected = connected
        
        # Update GUI elements in main thread
        self.root.after(0, self._update_connection_ui, connected)
    
    def _update_connection_ui(self, connected: bool):
        """Update UI elements based on connection status"""
        if connected:
            self.connection_status_var.set("Connected")
            self.connect_btn.config(state='disabled')
            self.disconnect_btn.config(state='normal')
            
            # Enable control buttons
            for btn in self.control_buttons.values():
                btn.config(state='normal')
                
        else:
            self.connection_status_var.set("Disconnected")
            self.connect_btn.config(state='normal')
            self.disconnect_btn.config(state='disabled')
            
            # Disable control buttons
            for btn in self.control_buttons.values():
                btn.config(state='disabled')
    
    def on_telemetry_received(self, telemetry_data: str):
        """Handle received telemetry data"""
        self.root.after(0, self._update_telemetry_display, telemetry_data)
    
    def _update_telemetry_display(self, telemetry_data: str):
        """Update telemetry display in GUI"""
        # Parse telemetry data
        parsed_data = self.telemetry_parser.parse(telemetry_data)
        
        # Update status variables
        if parsed_data:
            self.status_vars['battery'].set(f"{parsed_data.get('battery', '--')}%")
            self.status_vars['altitude'].set(f"{parsed_data.get('altitude', '--')} cm")
            self.status_vars['speed'].set(f"{parsed_data.get('speed', '--')} cm/s")
            
            # Update video window telemetry if open
            if self.video_window and self.video_window.is_window_open():
                self.video_window.update_telemetry(parsed_data)
        
        # Update telemetry text area
        current_time = time.strftime("%H:%M:%S")
        self.telemetry_text.insert(tk.END, f"[{current_time}] {telemetry_data}\n")
        self.telemetry_text.see(tk.END)
        
        # Limit text length
        if int(self.telemetry_text.index('end-1c').split('.')[0]) > 100:
            self.telemetry_text.delete('1.0', '50.0')
    
    def log_message(self, message: str):
        """Add message to log display"""
        current_time = time.strftime("%H:%M:%S")
        self.root.after(0, self._add_log_message, f"[{current_time}] {message}")
    
    def _add_log_message(self, message: str):
        """Add message to log text area"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        
        # Limit log length
        if int(self.log_text.index('end-1c').split('.')[0]) > 100:
            self.log_text.delete('1.0', '50.0')
    
    def takeoff_drone(self):
        """Initiate drone takeoff"""
        if self.controller:
            def takeoff_thread():
                if self.controller.takeoff():
                    self.log_message("Takeoff successful")
                    self.root.after(0, lambda: self.status_vars['flying'].set("Yes"))
                else:
                    self.log_message("Takeoff failed")
            
            threading.Thread(target=takeoff_thread, daemon=True).start()
    
    def land_drone(self):
        """Initiate drone landing"""
        if self.controller:
            def land_thread():
                if self.controller.land():
                    self.log_message("Landing successful")
                    self.root.after(0, lambda: self.status_vars['flying'].set("No"))
                else:
                    self.log_message("Landing failed")
            
            threading.Thread(target=land_thread, daemon=True).start()
    
    def move_drone(self, direction: str):
        """Move drone in specified direction"""
        if not self.controller:
            return
        
        distance = 30  # Default movement distance in cm
        
        def move_thread():
            success = False
            if direction == 'forward':
                success = self.controller.move_forward(distance)
            elif direction == 'backward':
                success = self.controller.move_backward(distance)
            elif direction == 'left':
                success = self.controller.move_left(distance)
            elif direction == 'right':
                success = self.controller.move_right(distance)
            elif direction == 'up':
                success = self.controller.move_up(distance)
            elif direction == 'down':
                success = self.controller.move_down(distance)
            
            if success:
                self.log_message(f"Moved {direction} {distance}cm")
            else:
                self.log_message(f"Failed to move {direction}")
        
        threading.Thread(target=move_thread, daemon=True).start()
    
    def rotate_drone(self, direction: str):
        """Rotate drone in specified direction"""
        if not self.controller:
            return
        
        degrees = 45  # Default rotation in degrees
        
        def rotate_thread():
            success = False
            if direction == 'left':
                success = self.controller.rotate_counterclockwise(degrees)
            elif direction == 'right':
                success = self.controller.rotate_clockwise(degrees)
            
            if success:
                self.log_message(f"Rotated {direction} {degrees}°")
            else:
                self.log_message(f"Failed to rotate {direction}")
        
        threading.Thread(target=rotate_thread, daemon=True).start()
    
    def update_speed(self, value):
        """Update drone speed setting"""
        speed = int(float(value))
        self.speed_label.config(text=str(speed))
        
        if self.controller:
            def speed_thread():
                if self.controller.set_speed(speed):
                    self.log_message(f"Speed set to {speed}")
                else:
                    self.log_message("Failed to set speed")
            
            threading.Thread(target=speed_thread, daemon=True).start()
    
    def emergency_stop(self):
        """Execute emergency stop"""
        if self.controller:
            if messagebox.askyesno("Emergency Stop", "Are you sure you want to execute emergency stop?"):
                self.controller.emergency_stop()
                self.log_message("EMERGENCY STOP EXECUTED")
                self.status_vars['flying'].set("No")
    
    def update_gui(self):
        """Main GUI update loop"""
        try:
            # Update drone status
            if self.controller:
                status = self.controller.get_flight_status()
                self.status_vars['mode'].set(status['mode'])
                
                if status['battery'] > 0:
                    self.status_vars['battery'].set(f"{status['battery']}%")
                
                if status['altitude'] > 0:
                    self.status_vars['altitude'].set(f"{status['altitude']} cm")
                
                self.status_vars['flying'].set("Yes" if status['is_flying'] else "No")
            
            # Schedule next update
            self.root.after(1000, self.update_gui)
            
        except Exception as e:
            self.logger.error(f"GUI update error: {e}")
    
    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            if self.connection:
                self.connection.disconnect()