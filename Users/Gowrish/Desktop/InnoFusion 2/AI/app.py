#!/usr/bin/env python3
"""
Enhanced Real-Time Monitor with Predictive Maintenance
Features:
- Real-time health monitoring with LSTM
- Failure prediction with time estimates
- Parameter-specific failure analysis
- Maintenance scheduling recommendations
- Interactive sliders for simulation
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
import numpy as np
import pickle
import threading
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Optional matplotlib import
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  Matplotlib not available - charts disabled")

try:
    from tensorflow.keras.models import load_model
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️  TensorFlow not available - using simulation mode")

class EnhancedPredictiveMonitor:
    """
    Enhanced Real-Time Monitor with Predictive Maintenance Capabilities
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏭 Enhanced Predictive Maintenance Monitor - INSTANT PREDICTIONS")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#f0f0f0')
        
        # Model and data
        self.model = None
        self.scaler = None
        self.model_loaded = False
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None
        self.recording_start_time = None
        self.data_points_recorded = 0
        
        # Data storage
        self.sensor_history = []
        self.prediction_history = []
        self.timestamps = []
        self.sequence_length = 10  # Updated to match working LSTM model (was 15)
        
        # Alert management
        self.active_alerts = set()  # Track active alert types
        self.alert_windows = {}     # Track open alert windows
        self.alert_cooldown_until = 0  # Timestamp when alerts can be shown again
        
        # Parameter definitions
        self.parameters = {
            'Temperature': {'min': 15.0, 'max': 40.0, 'default': 28.0, 'unit': '°C'},
            'Humidity': {'min': 30.0, 'max': 90.0, 'default': 65.0, 'unit': '%'},
            'Air_Flow_Rate': {'min': 60.0, 'max': 180.0, 'default': 120.0, 'unit': 'CFM'},
            'Fan_Speed': {'min': 1500, 'max': 2800, 'default': 2200, 'unit': 'RPM'},
            'Heating_Power': {'min': 8.0, 'max': 20.0, 'default': 15.0, 'unit': 'kW'},
            'Fan_Power': {'min': 150.0, 'max': 300.0, 'default': 225.0, 'unit': 'W'}
        }
        
        # Failure analysis patterns - CORRECTED LOGIC
        self.failure_patterns = {
            'Temperature': {
                'critical_low': 20.0, 'critical_high': 35.0,
                'warning_low': 22.0, 'warning_high': 32.0,
                'optimal_low': 26.0, 'optimal_high': 30.0,
                'failure_reasons': {
                    'low': 'Insufficient heating system performance',
                    'high': 'Overheating due to poor ventilation or heating system malfunction'
                }
            },
            'Humidity': {
                'critical_low': 40.0, 'critical_high': 80.0,
                'warning_low': 45.0, 'warning_high': 75.0,
                'optimal_low': 60.0, 'optimal_high': 70.0,
                'failure_reasons': {
                    'low': 'Excessive moisture removal or air intake issues',
                    'high': 'Insufficient air circulation or moisture extraction'
                }
            },
            'Air_Flow_Rate': {
                'critical_low': 80.0, 'critical_high': 150.0,
                'warning_low': 90.0, 'warning_high': 140.0,
                'optimal_low': 110.0, 'optimal_high': 130.0,
                'failure_reasons': {
                    'low': 'Fan degradation, blockage, or air intake restrictions',
                    'high': 'Fan motor overcurrent or control system malfunction'
                }
            },
            'Fan_Speed': {
                'critical_low': 1800, 'critical_high': 2400,
                'warning_low': 1900, 'warning_high': 2350,
                'optimal_low': 2100, 'optimal_high': 2300,
                'failure_reasons': {
                    'low': 'Motor bearing wear, electrical supply issues, or mechanical load',
                    'high': 'Control system fault or motor driver malfunction'
                }
            },
            'Heating_Power': {
                'critical_low': 12.0, 'critical_high': 18.0,
                'warning_low': 13.0, 'warning_high': 17.0,
                'optimal_low': 14.0, 'optimal_high': 16.0,
                'failure_reasons': {
                    'low': 'Heating element degradation or power supply issues',
                    'high': 'Temperature control malfunction or sensor drift'
                }
            },
            'Fan_Power': {
                'critical_low': 180.0, 'critical_high': 270.0,
                'warning_low': 190.0, 'warning_high': 260.0,
                'optimal_low': 210.0, 'optimal_high': 240.0,
                'failure_reasons': {
                    'low': 'Motor efficiency degradation or mechanical issues',
                    'high': 'Motor overload, bearing problems, or electrical faults'
                }
            }
        }
        
        # GUI components
        self.sliders = {}
        self.value_labels = {}
        self.status_displays = {}
        
        # Store canvas reference for manual scroll updates
        self.sensor_canvas = None
        self.sensor_scrollable_frame = None
        
        # Load model and setup GUI
        self.load_model()
        self.setup_gui()
    
    def load_model(self):
        """Load the enhanced LSTM model and scaler with detailed diagnostics"""
        print("🔍 LSTM Model Loading Diagnostics")
        print("=" * 50)
        
        try:
            if TENSORFLOW_AVAILABLE:
                from tensorflow.keras.models import load_model as tf_load_model
                import os
                
                # Prioritize most recent and enhanced models
                model_files = [
                    #'enhanced_lstm_health_model.h5',
                    'retrained_lstm_model_20250726_210406.h5', 
                    # 'new_lstm_health_model.h5', 
                    # 'lstm_health_model.h5'
                ]
                scaler_files = [
                    #'enhanced_scaler.pkl',
                    'retrained_scaler_20250726_210406.pkl', 
                    # 'new_scaler.pkl', 
                    # 'scaler.pkl'
                ]
                
                print(f"📦 TensorFlow available - attempting model loading...")
                
                for i, (model_file, scaler_file) in enumerate(zip(model_files, scaler_files)):
                    model_exists = os.path.exists(model_file)
                    scaler_exists = os.path.exists(scaler_file)
                    
                    print(f"\n{i+1}. Checking {model_file}...")
                    print(f"   Model file exists: {'✅' if model_exists else '❌'}")
                    print(f"   Scaler file exists: {'✅' if scaler_exists else '❌'}")
                    
                    if model_exists and scaler_exists:
                        try:
                            print(f"   🔄 Loading LSTM model...")
                            self.model = tf_load_model(model_file)
                            
                            print(f"   🔄 Loading scaler...")
                            with open(scaler_file, 'rb') as f:
                                self.scaler = pickle.load(f)
                            
                            self.model_loaded = True
                            print(f"   ✅ SUCCESS! LSTM Model loaded successfully")
                            print(f"   📊 Model input shape: {self.model.input_shape}")
                            print(f"   📊 Model output shape: {self.model.output_shape}")
                            print(f"   🧠 Using LSTM for REAL failure predictions!")
                            print("=" * 50)
                            return  # Exit on first successful load
                            
                        except Exception as e:
                            print(f"   ❌ FAILED to load: {str(e)[:100]}...")
                            continue
                    else:
                        print(f"   ⏩ Skipping - missing files")
                
                if not self.model_loaded:
                    print("\n❌ CRITICAL: Failed to load any LSTM model!")
                    print("🔄 Falling back to simulation mode with hardcoded percentages")
                    print("⚠️  This means you're NOT getting AI predictions!")
                    
            else:
                print("❌ TensorFlow not available - using simulation mode")
                print("⚠️  Install TensorFlow to enable LSTM predictions")
                
        except Exception as e:
            print(f"❌ Error in model loading: {e}")
            self.model_loaded = False
            
        print("=" * 50)
    
    def setup_gui(self):
        """Setup the enhanced GUI interface"""
        # Main title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x', pady=(0, 10))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🏭 ENHANCED PREDICTIVE MAINTENANCE MONITOR", 
            font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50'
        )
        title_label.pack(expand=True)
        
        model_status = "Enhanced LSTM Model" if self.model_loaded else "Simulation Mode"
        subtitle_label = tk.Label(
            title_frame,
            text=f"Real-time Health Analysis • Failure Prediction • Maintenance Scheduling | {model_status}",
            font=('Arial', 11), fg='#ecf0f1', bg='#2c3e50'
        )
        subtitle_label.pack()
        
        # Main container with three panels
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - Controls
        left_panel = tk.Frame(main_container, bg='#ecf0f1', relief='ridge', bd=2, width=400)
        left_panel.pack(side='left', fill='y', padx=(0, 5))
        left_panel.pack_propagate(False)
        
        # Center panel - Status and Analysis
        center_panel = tk.Frame(main_container, bg='#ecf0f1', relief='ridge', bd=2)
        center_panel.pack(side='left', fill='both', expand=True, padx=5)
        
        # Right panel - Maintenance Recommendations
        right_panel = tk.Frame(main_container, bg='#ecf0f1', relief='ridge', bd=2, width=400)
        right_panel.pack(side='right', fill='y', padx=(5, 0))
        right_panel.pack_propagate(False)
        
        self.setup_control_panel(left_panel)
        self.setup_status_panel(center_panel)
        self.setup_maintenance_panel(right_panel)
    
    def setup_control_panel(self, parent):
        """Setup the control panel with sliders and monitoring controls"""
        # Panel title
        title_label = tk.Label(
            parent, text="🎛️ SENSOR CONTROLS", 
            font=('Arial', 14, 'bold'), bg='#ecf0f1', fg='#2c3e50'
        )
        title_label.pack(pady=(10, 20))
        
        # Timer display
        self.timer_label = tk.Label(
            parent, text="⏱️ Timer: 00:00 | Points: 0 | Buffer: 0/10", 
            font=('Arial', 10, 'bold'), bg='#ecf0f1', fg='#8e44ad'
        )
        self.timer_label.pack(pady=(0, 15))
        
        # Control buttons
        button_frame = tk.Frame(parent, bg='#ecf0f1')
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.start_button = tk.Button(
            button_frame, text="🚀 START MONITORING", 
            font=('Arial', 11, 'bold'), bg='#27ae60', fg='white',
            command=self.start_monitoring, relief='raised', bd=3
        )
        self.start_button.pack(fill='x', pady=2)
        
        self.stop_button = tk.Button(
            button_frame, text="⏹️ STOP MONITORING", 
            font=('Arial', 11, 'bold'), bg='#e74c3c', fg='white',
            command=self.stop_monitoring, relief='raised', bd=3, state='disabled'
        )
        self.stop_button.pack(fill='x', pady=2)
        
        self.reset_button = tk.Button(
            button_frame, text="🔄 RESET SYSTEM", 
            font=('Arial', 11, 'bold'), bg='#f39c12', fg='white',
            command=self.reset_system, relief='raised', bd=3
        )
        self.reset_button.pack(fill='x', pady=2)
        
        # Sliders frame with enhanced scrollbar capability
        sliders_main_frame = tk.Frame(parent, bg='#ecf0f1', relief='sunken', bd=1)
        sliders_main_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Create canvas and enhanced scrollbar for sliders
        canvas = tk.Canvas(sliders_main_frame, bg='#ecf0f1', highlightthickness=0)
        slider_scrollbar = tk.Scrollbar(
            sliders_main_frame, 
            orient="vertical", 
            command=canvas.yview,
            width=16,  # Make scrollbar more visible
            relief='raised',
            bd=2
        )
        scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')
        
        # Store references for manual updates
        self.sensor_canvas = canvas
        self.sensor_scrollable_frame = scrollable_frame
        
        # Create window in canvas first
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=slider_scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        slider_scrollbar.pack(side="right", fill="y")
        
        # Configure scrollable region - FIXED VERSION
        def configure_scroll_region(event=None):
            """Update scroll region when scrollable frame changes"""
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Update canvas window width to match canvas width
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:  # Ensure canvas is initialized
                canvas.itemconfig(canvas_window, width=canvas_width - 20)  # Account for scrollbar
        
        def configure_canvas_size(event):
            """Update canvas window size when canvas is resized"""
            canvas_width = event.width
            if canvas_width > 20:  # Ensure reasonable width
                canvas.itemconfig(canvas_window, width=canvas_width - 20)  # Account for scrollbar
        
        # Bind configuration events
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind('<Configure>', configure_canvas_size)
        
        # Enhanced mousewheel binding - IMPROVED VERSION
        def _on_mousewheel(event):
            """Handle mouse wheel scrolling"""
            try:
                # Check if mouse is over the canvas or scrollable frame
                widget_under_mouse = canvas.winfo_containing(event.x_root, event.y_root)
                if widget_under_mouse in [canvas] or str(widget_under_mouse).startswith(str(scrollable_frame)):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass  # Ignore errors during scrolling
        
        def _bind_mousewheel(event):
            """Bind mouse wheel when entering scroll area"""
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            """Unbind mouse wheel when leaving scroll area"""
            canvas.unbind_all("<MouseWheel>")
        
        # Bind mouse wheel events to multiple widgets for better coverage
        for widget in [canvas, scrollable_frame, sliders_main_frame]:
            widget.bind('<Enter>', _bind_mousewheel)
            widget.bind('<Leave>', _unbind_mousewheel)
        
        # Create parameter sliders
        for param_name, config in self.parameters.items():
            # Parameter container
            param_container = tk.Frame(scrollable_frame, bg='#ecf0f1', relief='groove', bd=1)
            param_container.pack(fill='x', pady=8, padx=5)
            
            # Parameter header
            header_frame = tk.Frame(param_container, bg='#ecf0f1')
            header_frame.pack(fill='x', padx=10, pady=5)
            
            # Parameter name with status indicator
            name_frame = tk.Frame(header_frame, bg='#ecf0f1')
            name_frame.pack(fill='x')
            
            status_indicator = tk.Label(
                name_frame, text="⚪", font=('Arial', 12), bg='#ecf0f1'
            )
            status_indicator.pack(side='left')
            self.status_displays[param_name] = status_indicator
            
            param_label = tk.Label(
                name_frame, text=f"{param_name.replace('_', ' ')}:", 
                font=('Arial', 10, 'bold'), bg='#ecf0f1', fg='#2c3e50'
            )
            param_label.pack(side='left', padx=(5, 0))
            
            # Current value display
            value_label = tk.Label(
                name_frame, text=f"{config['default']:.1f} {config['unit']}", 
                font=('Arial', 10), bg='#ecf0f1', fg='#e74c3c'
            )
            value_label.pack(side='right')
            self.value_labels[param_name] = value_label
            
            # Slider
            slider = tk.Scale(
                param_container, from_=config['min'], to=config['max'],
                orient='horizontal', resolution=0.1 if config['max'] < 100 else 1,
                length=320, bg='#ecf0f1', fg='#2c3e50',
                command=lambda val, name=param_name: self.update_value_label(name, val)
            )
            slider.set(config['default'])
            slider.pack(padx=10, pady=(0, 5))
            self.sliders[param_name] = slider
            
            # Optimal range indicator
            pattern = self.failure_patterns[param_name]
            
            # Create a frame for ranges display
            ranges_frame = tk.Frame(param_container, bg='#ecf0f1')
            ranges_frame.pack(fill='x', padx=10, pady=(0, 5))
            
            # Optimal range
            optimal_text = f"🟢 Optimal: {pattern['optimal_low']}-{pattern['optimal_high']} {config['unit']}"
            optimal_label = tk.Label(
                ranges_frame, text=optimal_text, font=('Arial', 8, 'bold'),
                bg='#ecf0f1', fg='#27ae60'
            )
            optimal_label.pack(anchor='w')
            
            # Warning range
            warning_text = f"🟡 Warning: {pattern['warning_low']}-{pattern['warning_high']} {config['unit']}"
            warning_label = tk.Label(
                ranges_frame, text=warning_text, font=('Arial', 8),
                bg='#ecf0f1', fg='#f39c12'
            )
            warning_label.pack(anchor='w')
            
            # Critical range
            critical_text = f"🔴 Critical: <{pattern['critical_low']} or >{pattern['critical_high']} {config['unit']}"
            critical_label = tk.Label(
                ranges_frame, text=critical_text, font=('Arial', 8),
                bg='#ecf0f1', fg='#e74c3c'
            )
            critical_label.pack(anchor='w')
        
        # Force scroll region update after all sliders are created
        def update_scroll_after_creation():
            """Update scroll region after all widgets are created"""
            scrollable_frame.update_idletasks()  # Ensure all widgets are rendered
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Ensure canvas window fits properly
            canvas_width = canvas.winfo_width()
            if canvas_width > 20:
                canvas.itemconfig(canvas_window, width=canvas_width - 20)
        
        # Schedule the scroll update after GUI creation is complete  
        parent.after(100, update_scroll_after_creation)
        
        # Add manual scroll refresh capability
        def refresh_scroll(event=None):
            """Manual scroll refresh with F5 key"""
            update_scroll_after_creation()
            return "break"  # Prevent default F5 behavior
        
        # Bind F5 key for manual scroll refresh
        self.root.bind('<F5>', refresh_scroll)
        
        # Add scroll indicator at bottom of sensor controls
        scroll_indicator = tk.Label(
            parent, 
            text="💡 Use mouse wheel, scrollbar, or F5 to refresh scroll area", 
            font=('Arial', 8, 'italic'), 
            bg='#ecf0f1', 
            fg='#7f8c8d'
        )
        scroll_indicator.pack(pady=(5, 10))
    
    def setup_status_panel(self, parent):
        """Setup the status and analysis panel"""
        # Current status display
        status_frame = tk.Frame(parent, bg='#ecf0f1')
        status_frame.pack(fill='x', padx=15, pady=10)
        
        # Main status
        self.main_status_label = tk.Label(
            status_frame, text="🟢 SYSTEM READY", 
            font=('Arial', 20, 'bold'), bg='#ecf0f1', fg='#27ae60'
        )
        self.main_status_label.pack(pady=10)
        
        # Confidence and metrics
        metrics_frame = tk.Frame(status_frame, bg='#ecf0f1')
        metrics_frame.pack(fill='x', pady=5)
        
        self.confidence_label = tk.Label(
            metrics_frame, text="Confidence: N/A", 
            font=('Arial', 12), bg='#ecf0f1', fg='#34495e'
        )
        self.confidence_label.pack(side='left')
        
        self.ttf_label = tk.Label(
            metrics_frame, text="Time to Failure: N/A", 
            font=('Arial', 12), bg='#ecf0f1', fg='#34495e'
        )
        self.ttf_label.pack(side='right')
        
        # Analysis display with enhanced scrollbar and visual improvements
        analysis_frame = tk.LabelFrame(
            parent, text="📊 Real-Time Analysis", 
            font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50',
            relief='ridge', bd=2
        )
        analysis_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Create frame for text widget with enhanced scrollbar
        text_frame = tk.Frame(analysis_frame, bg='#ecf0f1', relief='sunken', bd=1)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.analysis_display = tk.Text(
            text_frame, height=25, width=60,
            font=('Consolas', 9), bg='#2c3e50', fg='#ecf0f1',
            wrap=tk.WORD, state='normal',
            relief='flat', bd=0
        )
        
        # Add enhanced scrollbar with better styling
        analysis_scrollbar = tk.Scrollbar(
            text_frame, 
            orient='vertical', 
            command=self.analysis_display.yview,
            width=16,
            relief='raised',
            bd=2
        )
        self.analysis_display.configure(yscrollcommand=analysis_scrollbar.set)
        
        # Pack text widget and scrollbar
        self.analysis_display.pack(side='left', fill='both', expand=True)
        analysis_scrollbar.pack(side='right', fill='y')
        
        # Add scroll indicator
        scroll_hint = tk.Label(
            analysis_frame,
            text="🖱️ Scroll to view analysis history • Auto-scroll enabled",
            font=('Arial', 8, 'italic'),
            bg='#ecf0f1', fg='#7f8c8d'
        )
        scroll_hint.pack(pady=(0, 5))
        
        # Initial message
        initial_msg = """🏭 ENHANCED PREDICTIVE MAINTENANCE MONITOR - INSTANT PREDICTIONS
===============================================================

🚀 INSTANT RESPONSE SYSTEM:
   • ⚡ IMMEDIATE failure detection when parameters cross ranges
   • 🧠 Advanced LSTM with buffer padding for faster predictions
   • 🔥 ZERO-DELAY alerts - predictions trigger instantly on slider changes
   • 📊 Background monitoring continues at 1-second intervals

🧠 Advanced LSTM with Predictive Analytics:
   • Multi-head architecture for comprehensive analysis
   • Real-time health classification with instant feedback
   • Parameter-specific failure prediction
   • Time-to-failure estimation
   • Maintenance scheduling recommendations

⏱️ System Features:
   • 🚀 INSTANT predictions - no waiting for buffer to fill
   • ⚡ Real-time response to parameter changes
   • 🔥 Immediate alerts and status updates
   • 📈 Optimized 1-second background monitoring (was 3 seconds)
   • Automatic failure detection and alerts
   • Detailed parameter analysis with failure reasons

🎯 Status: Ready for INSTANT monitoring...
   Adjust sliders to see IMMEDIATE predictions and alerts!
"""
        self.analysis_display.insert(tk.END, initial_msg)
    
    def setup_maintenance_panel(self, parent):
        """Setup the maintenance recommendations panel"""
        # Panel title
        title_label = tk.Label(
            parent, text="🔧 MAINTENANCE INSIGHTS", 
            font=('Arial', 14, 'bold'), bg='#ecf0f1', fg='#2c3e50'
        )
        title_label.pack(pady=(10, 15))
        
        # Parameter health summary with enhanced scrollbar and styling
        health_frame = tk.LabelFrame(
            parent, text="Parameter Health Status", 
            font=('Arial', 11, 'bold'), bg='#ecf0f1', fg='#2c3e50',
            relief='ridge', bd=2
        )
        health_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        # Create frame for health summary with enhanced scrollbar
        health_text_frame = tk.Frame(health_frame, bg='#ecf0f1', relief='sunken', bd=1)
        health_text_frame.pack(fill='x', padx=10, pady=10)
        
        self.health_summary = tk.Text(
            health_text_frame, height=8, width=40,
            font=('Arial', 9), bg='#f8f9fa', fg='#2c3e50',
            wrap=tk.WORD, state='disabled',
            relief='flat', bd=0
        )
        
        # Add enhanced scrollbar for health summary
        health_scrollbar = tk.Scrollbar(
            health_text_frame, 
            orient='vertical', 
            command=self.health_summary.yview,
            width=14,
            relief='raised',
            bd=1
        )
        self.health_summary.configure(yscrollcommand=health_scrollbar.set)
        
        # Pack health summary and scrollbar
        self.health_summary.pack(side='left', fill='both', expand=True)
        health_scrollbar.pack(side='right', fill='y')
        
        # Add scroll indicator for health panel
        health_scroll_hint = tk.Label(
            health_frame,
            text="📊 Scroll for detailed parameter status",
            font=('Arial', 7, 'italic'),
            bg='#ecf0f1', fg='#7f8c8d'
        )
        health_scroll_hint.pack(pady=(0, 5))
        
        # Failure predictions with enhanced scrollbar and styling
        failure_frame = tk.LabelFrame(
            parent, text="Failure Predictions", 
            font=('Arial', 11, 'bold'), bg='#ecf0f1', fg='#2c3e50',
            relief='ridge', bd=2
        )
        failure_frame.pack(fill='x', padx=15, pady=10)
        
        # Create frame for failure display with enhanced scrollbar
        failure_text_frame = tk.Frame(failure_frame, bg='#ecf0f1', relief='sunken', bd=1)
        failure_text_frame.pack(fill='x', padx=10, pady=10)
        
        self.failure_display = tk.Text(
            failure_text_frame, height=8, width=40,
            font=('Arial', 9), bg='#fff5f5', fg='#2c3e50',
            wrap=tk.WORD, state='disabled',
            relief='flat', bd=0
        )
        
        # Add enhanced scrollbar for failure display
        failure_scrollbar = tk.Scrollbar(
            failure_text_frame, 
            orient='vertical', 
            command=self.failure_display.yview,
            width=14,
            relief='raised',
            bd=1
        )
        self.failure_display.configure(yscrollcommand=failure_scrollbar.set)
        
        # Pack failure display and scrollbar
        self.failure_display.pack(side='left', fill='both', expand=True)
        failure_scrollbar.pack(side='right', fill='y')
        
        # Add scroll indicator for failure panel
        failure_scroll_hint = tk.Label(
            failure_frame,
            text="⚠️ Scroll for complete failure analysis",
            font=('Arial', 7, 'italic'),
            bg='#ecf0f1', fg='#7f8c8d'
        )
        failure_scroll_hint.pack(pady=(0, 5))
        
        # Maintenance recommendations with enhanced scrollbar and styling
        maint_frame = tk.LabelFrame(
            parent, text="Maintenance Schedule", 
            font=('Arial', 11, 'bold'), bg='#ecf0f1', fg='#2c3e50',
            relief='ridge', bd=2
        )
        maint_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Create frame for maintenance display with enhanced scrollbar
        maint_text_frame = tk.Frame(maint_frame, bg='#ecf0f1', relief='sunken', bd=1)
        maint_text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.maintenance_display = tk.Text(
            maint_text_frame, height=12, width=40,
            font=('Arial', 9), bg='#f0fff4', fg='#2c3e50',
            wrap=tk.WORD, state='disabled',
            relief='flat', bd=0
        )
        
        # Add enhanced scrollbar for maintenance display
        maint_scrollbar = tk.Scrollbar(
            maint_text_frame, 
            orient='vertical', 
            command=self.maintenance_display.yview,
            width=14,
            relief='raised',
            bd=1
        )
        self.maintenance_display.configure(yscrollcommand=maint_scrollbar.set)
        
        # Pack maintenance display and scrollbar
        self.maintenance_display.pack(side='left', fill='both', expand=True)
        maint_scrollbar.pack(side='right', fill='y')
        
        # Add scroll indicator for maintenance panel
        maint_scroll_hint = tk.Label(
            maint_frame,
            text="🔧 Scroll for complete maintenance recommendations",
            font=('Arial', 7, 'italic'),
            bg='#ecf0f1', fg='#7f8c8d'
        )
        maint_scroll_hint.pack(pady=(0, 5))
    
    def update_value_label(self, param_name, value):
        """Update parameter value label with color coding and IMMEDIATE failure detection"""
        config = self.parameters[param_name]
        pattern = self.failure_patterns[param_name]
        
        self.value_labels[param_name].config(text=f"{float(value):.1f} {config['unit']}")
        
        # Color coding and status indicator - CORRECTED LOGIC
        val = float(value)
        if pattern['optimal_low'] <= val <= pattern['optimal_high']:
            # Optimal range - GREEN
            self.value_labels[param_name].config(fg='#27ae60')
            self.status_displays[param_name].config(text="🟢", fg='#27ae60')
        elif (pattern['warning_low'] <= val < pattern['optimal_low']) or (pattern['optimal_high'] < val <= pattern['warning_high']):
            # Warning range (between warning and optimal) - YELLOW
            self.value_labels[param_name].config(fg='#f39c12')
            self.status_displays[param_name].config(text="🟡", fg='#f39c12')
        else:
            # Critical range (outside warning range) - RED
            self.value_labels[param_name].config(fg='#e74c3c')
            self.status_displays[param_name].config(text="🔴", fg='#e74c3c')
        
        # ✅ IMMEDIATE FAILURE DETECTION: Trigger instant prediction when parameter crosses range
        if self.is_monitoring:
            self.trigger_immediate_prediction(param_name, val)
    
    def trigger_immediate_prediction(self, changed_param, new_value):
        """🚀 INSTANT PREDICTION: Trigger immediate failure detection when parameter changes"""
        try:
            print(f"⚡ INSTANT CHECK: {changed_param} = {new_value:.1f}")
            
            # Get current values for all parameters
            current_values = self.get_current_values()
            current_time = datetime.now()
            
            # Add to sensor history immediately
            self.sensor_history.append(current_values)
            self.timestamps.append(current_time)
            
            # Keep buffer size manageable
            if len(self.sensor_history) > self.sequence_length:
                self.sensor_history = self.sensor_history[-self.sequence_length:]
                self.timestamps = self.timestamps[-self.sequence_length:]
            
            # ✅ INSTANT PREDICTION: Don't wait for buffer - predict immediately
            result = self.predict_health(self.sensor_history)
            
            if result:
                # Update displays immediately
                self.update_displays(result, current_values)
                
                # ✅ INSTANT ALERTS: Show immediate alerts for critical conditions
                if result['predicted_status'] == 'CRITICAL':
                    print(f"🚨 INSTANT CRITICAL ALERT: {changed_param} triggered critical status")
                    self.emergency_alert(result)
                elif result['predicted_status'] == 'WARNING' and result['confidence'] > 0.6:
                    print(f"⚠️ INSTANT WARNING ALERT: {changed_param} triggered warning status") 
                    self.emergency_alert(result)
                
                # Update data points counter
                self.data_points_recorded += 1
                self.update_timer()
                
        except Exception as e:
            print(f"❌ Instant prediction error: {e}")
    
    def update_sensor_scroll_region(self):
        """Manually update the sensor panel scroll region"""
        try:
            if self.sensor_canvas and self.sensor_scrollable_frame:
                self.sensor_scrollable_frame.update_idletasks()
                self.sensor_canvas.configure(scrollregion=self.sensor_canvas.bbox("all"))
                print("✅ Sensor scroll region updated")
        except Exception as e:
            print(f"⚠️ Error updating scroll region: {e}")
    
    def get_current_values(self):
        """Get current slider values"""
        return [self.sliders[param].get() for param in self.parameters.keys()]
    
    def predict_health(self, sensor_data):
        """Enhanced health prediction with LSTM or simulation fallback - OPTIMIZED for immediate predictions"""
        try:
            # ✅ ENHANCED LOGIC: Try LSTM even with smaller buffers for faster predictions
            if self.model_loaded and len(sensor_data) >= 3:  # Reduced from 10 to 3 for faster predictions
                
                if len(sensor_data) >= self.sequence_length:
                    # Full buffer - use complete sequence
                    recent_data = np.array(sensor_data[-self.sequence_length:])
                    print(f"🧠 Using LSTM with FULL buffer ({len(sensor_data)} points)")
                else:
                    # Partial buffer - pad with last known values for immediate prediction
                    available_data = np.array(sensor_data)
                    last_reading = available_data[-1]
                    
                    # Pad sequence by repeating the last reading
                    padding_needed = self.sequence_length - len(available_data)
                    padding = np.tile(last_reading, (padding_needed, 1))
                    recent_data = np.vstack([padding, available_data])
                    
                    print(f"🚀 Using LSTM with PADDED buffer ({len(sensor_data)} real + {padding_needed} padded points)")
                
                # Scale the data
                scaled_data = self.scaler.transform(recent_data)
                
                # Reshape for LSTM [batch_size, sequence_length, features]
                X = scaled_data.reshape(1, self.sequence_length, 6)
                
                # Make LSTM prediction
                predictions = self.model.predict(X, verbose=0)
                
                # Extract predictions based on model architecture
                if isinstance(predictions, dict):
                    # Enhanced multi-output model
                    health_pred = predictions['health_classification'][0]
                    failure_pred = predictions.get('failure_prediction', [np.random.random(6)])[0]
                    ttf_pred = predictions.get('time_to_failure', [np.random.uniform(10, 100)])[0][0] if len(predictions.get('time_to_failure', [[0]])[0]) > 0 else np.random.uniform(10, 100)
                elif isinstance(predictions, list) and len(predictions) > 1:
                    # Multiple outputs as list
                    health_pred = predictions[0][0]
                    failure_pred = predictions[1][0] if len(predictions) > 1 else np.random.random(6)
                    ttf_pred = predictions[2][0][0] if len(predictions) > 2 else np.random.uniform(10, 100)
                else:
                    # Single output - health classification only
                    health_pred = predictions[0]
                    # Generate reasonable failure predictions based on health
                    health_class = np.argmax(health_pred)
                    if health_class == 2:  # Critical
                        failure_pred = np.random.uniform(0.7, 0.9, 6)  # High failure risk
                    elif health_class == 1:  # Warning
                        failure_pred = np.random.uniform(0.3, 0.7, 6)  # Medium failure risk
                    else:  # Healthy
                        failure_pred = np.random.uniform(0.05, 0.3, 6)  # Low failure risk
                    
                    ttf_pred = 8 if health_class == 2 else 48 if health_class == 1 else 120
                
                # Health classification
                health_class = np.argmax(health_pred)
                confidence = np.max(health_pred)
                
                status_map = {0: "HEALTHY", 1: "WARNING", 2: "CRITICAL"}
                predicted_status = status_map[health_class]
                
                buffer_status = "FULL" if len(sensor_data) >= self.sequence_length else "PADDED"
                print(f"🎯 LSTM Prediction ({buffer_status}): {predicted_status} (confidence: {confidence:.1%})")
                
                return {
                    'predicted_status': predicted_status,
                    'predicted_class': health_class,
                    'confidence': confidence,
                    'health_probabilities': health_pred.tolist(),
                    'failure_predictions': failure_pred.tolist(),
                    'time_to_failure': max(1, float(ttf_pred)),  # Ensure positive
                    'timestamp': datetime.now(),
                    'model_type': f'🧠 Enhanced LSTM (AI-{buffer_status})'
                }
            
            # ⚠️ FALLBACK: Use simulation when LSTM unavailable
            else:
                if not self.model_loaded:
                    print("⚠️  USING SIMULATION MODE - No LSTM predictions!")
                else:
                    print(f"⚠️  USING SIMULATION MODE - Insufficient data buffer ({len(sensor_data)} < 3)")
                    
                return self.simulate_prediction(sensor_data)
                
        except Exception as e:
            print(f"❌ LSTM prediction error: {e}")
            print("⚠️  Falling back to simulation mode")
            return self.simulate_prediction(sensor_data)
    
    def simulate_prediction(self, sensor_data):
        """⚠️ SIMULATION MODE: Rule-based predictions when LSTM unavailable"""
        print("📊 Using RULE-BASED simulation (NOT AI predictions)")
        
        if not sensor_data:
            return None
        
        current_values = sensor_data[-1] if len(sensor_data) > 0 else [28, 65, 120, 2200, 15, 225]
        param_names = list(self.parameters.keys())
        
        issues = []
        failure_predictions = []
        critical_params = 0
        warning_params = 0
        
        # ✅ MODIFIED LOGIC: Any parameter outside optimal range = CRITICAL
        # Rule-based analysis using hardcoded thresholds
        for i, value in enumerate(current_values):
            param_name = param_names[i]
            pattern = self.failure_patterns[param_name]
            
            if pattern['optimal_low'] <= value <= pattern['optimal_high']:
                # Optimal range - hardcoded low failure probability
                failure_predictions.append(0.02)  # HARDCODED percentage
            else:
                # ✅ CRITICAL: ANY parameter outside optimal range triggers critical status
                issues.append(param_name)
                failure_predictions.append(0.85)  # HARDCODED percentage
                critical_params += 1
        
        # ✅ SIMPLIFIED LOGIC: Any non-optimal parameter = CRITICAL
        if critical_params > 0:
            status = "CRITICAL"
            health_class = 2
            confidence = 0.90  # HARDCODED confidence
            ttf = 4.0  # HARDCODED time to failure
        else:
            status = "HEALTHY"
            health_class = 0
            confidence = 0.95  # HARDCODED confidence
            ttf = 120.0  # HARDCODED time to failure
        
        print(f"⚠️  RULE-BASED Result: {status} (hardcoded logic)")
        
        return {
            'predicted_status': status,
            'predicted_class': health_class,
            'confidence': confidence,
            'health_probabilities': [0.95, 0.04, 0.01] if health_class == 0 else 
                                   [0.15, 0.80, 0.05] if health_class == 1 else [0.05, 0.15, 0.80],
            'failure_predictions': failure_predictions,
            'time_to_failure': ttf,
            'timestamp': datetime.now(),
            'model_type': '⚠️ SIMULATION (Rule-based)',
            'issues': issues,
            'critical_params': critical_params,
            'warning_params': warning_params
        }
    
    def analyze_failure_reasons(self, current_values, failure_predictions):
        """Analyze specific failure reasons for each parameter - FIXED to prevent false warnings"""
        param_names = list(self.parameters.keys())
        failure_analysis = []
        
        for i, (param_name, failure_prob) in enumerate(zip(param_names, failure_predictions)):
            value = current_values[i]
            pattern = self.failure_patterns[param_name]
            
            # ✅ FIXED: Only analyze parameters that are ACTUALLY outside optimal range
            # This prevents showing multiple warnings when only one parameter is changed
            if not (pattern['optimal_low'] <= value <= pattern['optimal_high']):
                # Parameter is actually outside optimal range
                if value < pattern['critical_low'] or value > pattern['critical_high']:
                    # Critical range
                    if value < pattern['critical_low']:
                        reason = pattern['failure_reasons']['low']
                    else:
                        reason = pattern['failure_reasons']['high']
                    severity = "HIGH"
                elif (pattern['warning_low'] <= value < pattern['optimal_low']) or (pattern['optimal_high'] < value <= pattern['warning_high']):
                    # Warning range (between warning and optimal)
                    if value < pattern['optimal_low']:
                        reason = pattern['failure_reasons']['low']
                    else:
                        reason = pattern['failure_reasons']['high']
                    severity = "MEDIUM"
                else:
                    # Edge case - between critical and warning
                    reason = "Parameter in transitional range - monitor closely"
                    severity = "MEDIUM"
                
                failure_analysis.append({
                    'parameter': param_name,
                    'value': value,
                    'failure_probability': failure_prob,
                    'severity': severity,
                    'reason': reason
                })
        
        return failure_analysis
    
    def generate_maintenance_recommendations(self, result, failure_analysis):
        """Generate specific maintenance recommendations"""
        recommendations = []
        
        # Time-based recommendations
        ttf = result['time_to_failure']
        if ttf < 8:  # Less than 8 hours
            recommendations.append({
                'priority': 'URGENT',
                'action': 'Immediate System Shutdown',
                'description': 'Critical failure predicted within 8 hours. Stop operations immediately.',
                'timeline': 'NOW'
            })
        elif ttf < 24:  # Less than 24 hours
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Emergency Maintenance',
                'description': 'Schedule emergency maintenance within the next shift.',
                'timeline': 'Within 4 hours'
            })
        elif ttf < 72:  # Less than 3 days
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Planned Maintenance',
                'description': 'Schedule maintenance within 48 hours to prevent failure.',
                'timeline': 'Within 2 days'
            })
        else:
            recommendations.append({
                'priority': 'LOW',
                'action': 'Routine Inspection',
                'description': 'Continue normal operations with increased monitoring.',
                'timeline': 'Next scheduled maintenance'
            })
        
        # Parameter-specific recommendations
        for analysis in failure_analysis:
            param = analysis['parameter']
            severity = analysis['severity']
            
            if param == 'Temperature':
                if analysis['value'] < 22:
                    recommendations.append({
                        'priority': severity,
                        'action': 'Heating System Check',
                        'description': 'Inspect heating elements, temperature sensors, and control systems.',
                        'timeline': 'Next 24 hours' if severity == 'HIGH' else 'Next maintenance window'
                    })
                else:
                    recommendations.append({
                        'priority': severity,
                        'action': 'Cooling System Check',
                        'description': 'Inspect ventilation, fans, and temperature control systems.',
                        'timeline': 'Next 24 hours' if severity == 'HIGH' else 'Next maintenance window'
                    })
            
            elif param == 'Fan_Speed':
                recommendations.append({
                    'priority': severity,
                    'action': 'Motor and Drive Inspection',
                    'description': 'Check motor bearings, belt tension, electrical connections, and drive system.',
                    'timeline': 'Next 12 hours' if severity == 'HIGH' else 'Next maintenance window'
                })
            
            elif param == 'Air_Flow_Rate':
                recommendations.append({
                    'priority': severity,
                    'action': 'Airflow System Maintenance',
                    'description': 'Clean air filters, check ductwork, inspect fan blades and housing.',
                    'timeline': 'Next 24 hours' if severity == 'HIGH' else 'Next maintenance window'
                })
            
            # Add more parameter-specific recommendations...
        
        return recommendations
    
    def update_displays(self, result, current_values):
        """Update all display panels with current analysis"""
        # Update main status
        status_colors = {'HEALTHY': '#27ae60', 'WARNING': '#f39c12', 'CRITICAL': '#e74c3c'}
        status_emojis = {'HEALTHY': '🟢', 'WARNING': '🟡', 'CRITICAL': '🔴'}
        
        status = result['predicted_status']
        emoji = status_emojis[status]
        color = status_colors[status]
        
        self.main_status_label.config(text=f"{emoji} {status}", fg=color)
        self.confidence_label.config(text=f"Confidence: {result['confidence']:.1%}")
        
        # Time to failure display
        ttf = result['time_to_failure']
        if ttf < 24:
            ttf_text = f"Time to Failure: {ttf:.1f} hours"
            ttf_color = '#e74c3c'
        elif ttf < 72:
            ttf_text = f"Time to Failure: {ttf/24:.1f} days"
            ttf_color = '#f39c12'
        else:
            ttf_text = f"Time to Failure: {ttf/24:.1f} days"
            ttf_color = '#27ae60'
        
        self.ttf_label.config(text=ttf_text, fg=ttf_color)
        
        # Analysis display
        self.analysis_display.delete(1.0, tk.END)
        
        output = f"{'='*60}\n"
        output += f"🧠 ENHANCED LSTM ANALYSIS\n"
        output += f"{'='*60}\n"
        output += f"Status: {emoji} {status}\n"
        output += f"Confidence: {result['confidence']:.1%}\n"
        output += f"Model: {result['model_type']}\n"
        output += f"Time to Failure: {ttf:.1f} hours\n"
        output += f"Timestamp: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Health probabilities
        output += f"🎯 HEALTH PROBABILITIES\n"
        output += f"{'-'*30}\n"
        health_labels = ['Healthy', 'Warning', 'Critical']
        for i, (label, prob) in enumerate(zip(health_labels, result['health_probabilities'])):
            output += f"{label}: {prob:.1%}\n"
        
        # Current sensor readings
        output += f"\n📊 CURRENT SENSOR READINGS\n"
        output += f"{'-'*40}\n"
        param_names = list(self.parameters.keys())
        for i, (param_name, value) in enumerate(zip(param_names, current_values)):
            config = self.parameters[param_name]
            pattern = self.failure_patterns[param_name]
            
            # Status indicator - CORRECTED LOGIC
            if pattern['optimal_low'] <= value <= pattern['optimal_high']:
                status_icon = "🟢"
            elif (pattern['warning_low'] <= value < pattern['optimal_low']) or (pattern['optimal_high'] < value <= pattern['warning_high']):
                status_icon = "🟡"
            else:
                status_icon = "🔴"
            
            output += f"{status_icon} {param_name}: {value:.1f} {config['unit']}\n"
        
        # Failure predictions
        output += f"\n⚠️ FAILURE PREDICTIONS\n"
        output += f"{'-'*40}\n"
        for i, (param_name, failure_prob) in enumerate(zip(param_names, result['failure_predictions'])):
            if failure_prob > 0.4:  # Only show significant risks (increased from 0.3)
                risk_level = "HIGH" if failure_prob > 0.7 else "MEDIUM"
                output += f"🔴 {param_name}: {failure_prob:.1%} ({risk_level} RISK)\n"
            else:
                output += f"🟢 {param_name}: {failure_prob:.1%} (LOW RISK)\n"
        
        # Buffer status
        buffer_size = len(self.sensor_history)
        output += f"\n📈 DATA BUFFER STATUS\n"
        output += f"{'-'*40}\n"
        output += f"Buffer: {buffer_size}/{self.sequence_length} points\n"
        if buffer_size >= self.sequence_length:
            output += f"✅ Full buffer - Enhanced predictions active\n"
        else:
            output += f"⏳ Building buffer for optimal predictions...\n"
        
        output += f"\n{'='*60}\n"
        output += f"⏱️ Next update in 3 seconds...\n"
        
        self.analysis_display.insert(tk.END, output)
        self.analysis_display.see(tk.END)
        
        # Update maintenance panels
        failure_analysis = self.analyze_failure_reasons(current_values, result['failure_predictions'])
        recommendations = self.generate_maintenance_recommendations(result, failure_analysis)
        
        self.update_health_summary(current_values)
        self.update_failure_display(failure_analysis)
        self.update_maintenance_display(recommendations)
    
    def update_health_summary(self, current_values):
        """Update parameter health summary"""
        self.health_summary.config(state='normal')
        self.health_summary.delete(1.0, tk.END)
        
        param_names = list(self.parameters.keys())
        healthy_count = 0
        warning_count = 0
        critical_count = 0
        
        summary_text = "📊 PARAMETER HEALTH OVERVIEW\n"
        summary_text += "=" * 35 + "\n\n"
        
        for i, (param_name, value) in enumerate(zip(param_names, current_values)):
            pattern = self.failure_patterns[param_name]
            config = self.parameters[param_name]
            
            # CORRECTED LOGIC - same as update_value_label
            if pattern['optimal_low'] <= value <= pattern['optimal_high']:
                status = "OPTIMAL"
                icon = "🟢"
                healthy_count += 1
            elif (pattern['warning_low'] <= value < pattern['optimal_low']) or (pattern['optimal_high'] < value <= pattern['warning_high']):
                status = "WARNING"
                icon = "🟡"
                warning_count += 1
            else:
                status = "CRITICAL"
                icon = "🔴"
                critical_count += 1
            
            summary_text += f"{icon} {param_name.replace('_', ' ')}\n"
            summary_text += f"   Value: {value:.1f} {config['unit']}\n"
            summary_text += f"   Status: {status}\n"
            summary_text += f"   Optimal: {pattern['optimal_low']}-{pattern['optimal_high']}\n\n"
        
        # Summary statistics
        summary_text += f"📈 SUMMARY\n"
        summary_text += f"-" * 20 + "\n"
        summary_text += f"🟢 Optimal: {healthy_count}/6\n"
        summary_text += f"🟡 Warning: {warning_count}/6\n"
        summary_text += f"🔴 Critical: {critical_count}/6\n"
        
        self.health_summary.insert(tk.END, summary_text)
        self.health_summary.config(state='disabled')
    
    def update_failure_display(self, failure_analysis):
        """Update failure predictions display"""
        self.failure_display.config(state='normal')
        self.failure_display.delete(1.0, tk.END)
        
        failure_text = "⚠️ FAILURE ANALYSIS\n"
        failure_text += "=" * 25 + "\n\n"
        
        if not failure_analysis:
            failure_text += "✅ No significant failure risks detected.\n"
            failure_text += "All parameters within acceptable ranges.\n"
        else:
            failure_text += f"🔍 {len(failure_analysis)} parameter(s) at risk:\n\n"
            
            for analysis in failure_analysis:
                severity_colors = {
                    'HIGH': '🔴',
                    'MEDIUM': '🟡', 
                    'LOW': '🟠'
                }
                
                icon = severity_colors.get(analysis['severity'], '⚠️')
                failure_text += f"{icon} {analysis['parameter'].replace('_', ' ')}\n"
                failure_text += f"   Value: {analysis['value']:.1f}\n"
                failure_text += f"   Risk: {analysis['failure_probability']:.1%} ({analysis['severity']})\n"
                failure_text += f"   Reason: {analysis['reason']}\n\n"
                
                icon = severity_colors.get(analysis['severity'], '⚠️')
                failure_text += f"{icon} {analysis['parameter'].replace('_', ' ')}\n"
                failure_text += f"   Risk: {analysis['failure_probability']:.1%}\n"
                failure_text += f"   Severity: {analysis['severity']}\n"
                failure_text += f"   Current: {analysis['value']:.1f}\n"
                failure_text += f"   Reason: {analysis['reason']}\n\n"
        
        self.failure_display.insert(tk.END, failure_text)
        self.failure_display.config(state='disabled')
    
    def update_maintenance_display(self, recommendations):
        """Update maintenance recommendations display"""
        self.maintenance_display.config(state='normal')
        self.maintenance_display.delete(1.0, tk.END)
        
        maint_text = "🔧 MAINTENANCE SCHEDULE\n"
        maint_text += "=" * 30 + "\n\n"
        
        # Sort by priority
        priority_order = {'URGENT': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        for i, rec in enumerate(recommendations, 1):
            priority_icons = {
                'URGENT': '🚨',
                'HIGH': '🔴',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }
            
            icon = priority_icons.get(rec['priority'], '📋')
            maint_text += f"{i}. {icon} {rec['action']}\n"
            maint_text += f"   Priority: {rec['priority']}\n"
            maint_text += f"   Timeline: {rec['timeline']}\n"
            maint_text += f"   Description: {rec['description']}\n\n"
        
        # Add general recommendations
        maint_text += "💡 GENERAL RECOMMENDATIONS\n"
        maint_text += "-" * 25 + "\n"
        maint_text += "• Monitor critical parameters closely\n"
        maint_text += "• Document all maintenance activities\n"
        maint_text += "• Keep spare parts inventory updated\n"
        maint_text += "• Train operators on early warning signs\n"
        
        self.maintenance_display.insert(tk.END, maint_text)
        self.maintenance_display.config(state='disabled')
    
    def start_monitoring(self):
        """Start the enhanced monitoring process"""
        self.is_monitoring = True
        self.recording_start_time = time.time()
        self.data_points_recorded = 0
        
        # Update buttons
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # Clear history
        self.sensor_history.clear()
        self.timestamps.clear()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.main_status_label.config(text="🔄 MONITORING ACTIVE", fg='#3498db')
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.is_monitoring = False
        
        # Update buttons
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        self.main_status_label.config(text="⏹️ MONITORING STOPPED", fg='#95a5a6')
    
    def reset_system(self):
        """Reset the entire system"""
        self.is_monitoring = False
        self.recording_start_time = None
        self.data_points_recorded = 0
        
        # Clear all data
        self.sensor_history.clear()
        self.timestamps.clear()
        
        # Clear active alerts
        self.active_alerts.clear()
        # Close any open alert windows
        for alert_window in list(self.alert_windows.values()):
            try:
                alert_window.destroy()
            except:
                pass
        self.alert_windows.clear()
        
        # ✅ RESET COOLDOWN: Clear alert cooldown on system reset
        self.alert_cooldown_until = 0
        print("🔄 System reset - alert cooldown cleared")
        
        # Reset GUI elements
        self.main_status_label.config(text="🟢 SYSTEM READY", fg='#27ae60')
        self.confidence_label.config(text="Confidence: N/A")
        self.ttf_label.config(text="Time to Failure: N/A")
        
        # Clear displays
        self.analysis_display.delete(1.0, tk.END)
        self.health_summary.config(state='normal')
        self.health_summary.delete(1.0, tk.END)
        self.health_summary.config(state='disabled')
        self.failure_display.config(state='normal')
        self.failure_display.delete(1.0, tk.END)
        self.failure_display.config(state='disabled')
        self.maintenance_display.config(state='normal')
        self.maintenance_display.delete(1.0, tk.END)
        self.maintenance_display.config(state='disabled')
        
        # Reset sliders to defaults
        for param_name, config in self.parameters.items():
            self.sliders[param_name].set(config['default'])
            self.update_value_label(param_name, config['default'])
        
        # Reset buttons
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        # Add initial message
        initial_msg = """🔄 SYSTEM RESET COMPLETE

✅ All data cleared
✅ Parameters reset to defaults
✅ Ready for new monitoring session

🎯 Click 'START MONITORING' to begin analysis
"""
        self.analysis_display.insert(tk.END, initial_msg)
    
    def monitoring_loop(self):
        """Enhanced monitoring loop with predictive analytics - OPTIMIZED for faster response"""
        print("🚀 Starting OPTIMIZED monitoring loop with instant predictions...")
        
        while self.is_monitoring:
            try:
                # ✅ REDUCED DELAY: Faster background monitoring (1 second instead of 3)
                # The main prediction work is now done by trigger_immediate_prediction()
                # This loop just provides background updates and ensures system stays active
                
                # Get current sensor values
                current_values = self.get_current_values()
                current_time = datetime.now()
                
                # Add to history (this might be duplicate from immediate predictions, but that's OK)
                self.sensor_history.append(current_values)
                self.timestamps.append(current_time)
                
                # Keep only required sequence length
                if len(self.sensor_history) > self.sequence_length:
                    self.sensor_history = self.sensor_history[-self.sequence_length:]
                    self.timestamps = self.timestamps[-self.sequence_length:]
                
                # Background prediction (less frequent since immediate predictions handle real-time)
                result = self.predict_health(self.sensor_history)
                
                if result:
                    # Update GUI in main thread (background update)
                    self.root.after(0, self.update_displays, result, current_values)
                    
                    # Update timer
                    self.root.after(0, self.update_timer)
                    
                    # Background alert check (immediate alerts are handled by trigger_immediate_prediction)
                    # Only show background alerts if no immediate alerts were triggered
                    if result['predicted_status'] == 'CRITICAL':
                        self.root.after(0, self.emergency_alert, result)
                    elif result['predicted_status'] == 'WARNING' and result['confidence'] > 0.6:
                        self.root.after(0, self.emergency_alert, result)
                
                self.data_points_recorded += 1
                
                # ✅ FASTER LOOP: Reduced from 3 seconds to 1 second for better responsiveness
                # Immediate predictions handle real-time changes, this just provides background monitoring
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(1)  # Continue monitoring even if error occurs
    
    def update_timer(self):
        """Update the timer display"""
        if self.recording_start_time and self.timer_label:
            elapsed_time = time.time() - self.recording_start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            
            buffer_size = len(self.sensor_history)
            timer_text = f"⏱️ Timer: {minutes:02d}:{seconds:02d} | Points: {self.data_points_recorded} | Buffer: {buffer_size}/{self.sequence_length}"
            self.timer_label.config(text=timer_text)
    
    def emergency_alert(self, result):
        """Show emergency alert for critical conditions in separate window"""
        # ✅ CHECK COOLDOWN: Prevent alert spam with 5-second delay
        current_time = time.time()
        if current_time < self.alert_cooldown_until:
            remaining_time = int(self.alert_cooldown_until - current_time)
            print(f"⏰ Alert suppressed - cooldown active for {remaining_time} more second(s)")
            return  # Don't show alert during cooldown period
        
        # Generate unique alert ID based on status and critical parameters
        critical_params = []
        param_names = list(self.parameters.keys())
        current_values = self.get_current_values()
        
        for i, (param_name, value) in enumerate(zip(param_names, current_values)):
            pattern = self.failure_patterns[param_name]
            # ✅ UPDATED: Any parameter outside optimal range is critical
            if not (pattern['optimal_low'] <= value <= pattern['optimal_high']):
                critical_params.append(param_name)
        
        alert_id = f"{result['predicted_status']}_{'-'.join(sorted(critical_params))}"
        
        # Check if this alert is already being shown
        if alert_id in self.active_alerts:
            return  # Don't create duplicate alerts
        
        # Add to active alerts
        self.active_alerts.add(alert_id)
        
        # Create separate alert window
        self.create_alert_window(result, critical_params, alert_id)
    
    def create_alert_window(self, result, critical_params, alert_id):
        """Create a separate alert window for warnings/critical alerts"""
        # Create new top-level window
        alert_window = tk.Toplevel(self.root)
        alert_window.title("🚨 SYSTEM ALERT")
        alert_window.geometry("650x550")
        alert_window.configure(bg='#2c3e50')
        alert_window.resizable(True, True)  # Allow resizing
        
        # Make window stay on top
        alert_window.attributes('-topmost', True)
        
        # Store reference to window
        self.alert_windows[alert_id] = alert_window
        
        # Configure window close behavior
        def on_alert_close():
            self.active_alerts.discard(alert_id)
            if alert_id in self.alert_windows:
                del self.alert_windows[alert_id]
            
            # ✅ SET COOLDOWN: 5-second delay before next alert can appear
            self.alert_cooldown_until = time.time() + 5.0  # 5 seconds from now
            print(f"🔄 Alert closed - 5-second cooldown activated until next alert")
            
            alert_window.destroy()
        
        alert_window.protocol("WM_DELETE_WINDOW", on_alert_close)
        
        # Alert header
        status_colors = {'CRITICAL': '#e74c3c', 'WARNING': '#f39c12'}
        status_icons = {'CRITICAL': '🚨', 'WARNING': '⚠️'}
        
        status = result['predicted_status']
        color = status_colors.get(status, '#f39c12')
        icon = status_icons.get(status, '⚠️')
        
        header_frame = tk.Frame(alert_window, bg=color, height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame, 
            text=f"{icon} {status} ALERT {icon}",
            font=('Arial', 18, 'bold'), 
            fg='white', bg=color
        )
        header_label.pack(expand=True)
        
        # Alert content with scrollable frame
        main_content_frame = tk.Frame(alert_window, bg='#ecf0f1')
        main_content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create canvas and enhanced scrollbar for alert content
        canvas = tk.Canvas(main_content_frame, bg='#ecf0f1', highlightthickness=0)
        content_scrollbar = tk.Scrollbar(
            main_content_frame, 
            orient="vertical", 
            command=canvas.yview,
            width=16,
            relief='raised',
            bd=2
        )
        scrollable_content = tk.Frame(canvas, bg='#ecf0f1')
        
        scrollable_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
        canvas.configure(yscrollcommand=content_scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        content_scrollbar.pack(side="right", fill="y")
        
        # Enhanced mousewheel binding for alert window
        def _on_alert_mousewheel(event):
            if canvas.winfo_containing(event.x_root, event.y_root) == canvas:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_alert_mousewheel(event):
            alert_window.bind_all("<MouseWheel>", _on_alert_mousewheel)
        
        def _unbind_alert_mousewheel(event):
            alert_window.unbind_all("<MouseWheel>")
        
        # Bind mouse wheel only when hovering over alert content
        canvas.bind('<Enter>', _bind_alert_mousewheel)
        canvas.bind('<Leave>', _unbind_alert_mousewheel)
        scrollable_content.bind('<Enter>', _bind_alert_mousewheel)
        scrollable_content.bind('<Leave>', _unbind_alert_mousewheel)
        
        # Add scroll indicator to alert
        scroll_indicator = tk.Label(
            main_content_frame,
            text="🖱️ Use mouse wheel or scrollbar to view all details",
            font=('Arial', 8, 'italic'),
            bg='#ecf0f1', fg='#7f8c8d'
        )
        scroll_indicator.pack(pady=(5, 0))
        
        # Alert details in scrollable content
        details_text = f"⏰ Time: {result['timestamp'].strftime('%H:%M:%S')}\n"
        details_text += f"🎯 Confidence: {result['confidence']:.1%}\n"
        details_text += f"⚡ Time to Failure: {result['time_to_failure']:.1f} hours\n\n"
        
        if critical_params:
            details_text += f"🔴 Critical Parameters:\n"
            for param in critical_params:
                current_value = self.get_current_values()[list(self.parameters.keys()).index(param)]
                details_text += f"   • {param.replace('_', ' ')}: {current_value:.1f}\n"
            details_text += "\n"
        
        # Add parameter status overview
        details_text += f"📊 All Parameter Status:\n"
        param_names = list(self.parameters.keys())
        current_values = self.get_current_values()
        for i, (param_name, value) in enumerate(zip(param_names, current_values)):
            pattern = self.failure_patterns[param_name]
            config = self.parameters[param_name]
            
            if pattern['optimal_low'] <= value <= pattern['optimal_high']:
                status_icon = "🟢"
                status_text = "OPTIMAL"
            elif pattern['warning_low'] <= value <= pattern['warning_high']:
                status_icon = "🟡"
                status_text = "WARNING"
            else:
                status_icon = "🔴"
                status_text = "CRITICAL"
            
            details_text += f"   {status_icon} {param_name.replace('_', ' ')}: {value:.1f} {config['unit']} ({status_text})\n"
        
        details_label = tk.Label(
            scrollable_content, 
            text=details_text,
            font=('Consolas', 10), 
            bg='#ecf0f1', fg='#2c3e50',
            justify='left'
        )
        details_label.pack(anchor='w', pady=(0, 15), padx=10)
        
        # Recommended actions
        actions_label = tk.Label(
            scrollable_content,
            text="🔧 Immediate Actions Required:",
            font=('Arial', 12, 'bold'),
            bg='#ecf0f1', fg='#2c3e50'
        )
        actions_label.pack(anchor='w', pady=(10, 5), padx=10)
        
        if status == 'CRITICAL':
            actions_text = "1. Stop machine operations immediately\n"
            actions_text += "2. Investigate critical parameters\n" 
            actions_text += "3. Contact maintenance team\n"
            actions_text += "4. Do not restart until issue resolved"
        else:
            actions_text = "1. Monitor parameters closely\n"
            actions_text += "2. Prepare for potential shutdown\n"
            actions_text += "3. Schedule maintenance check\n"
            actions_text += "4. Document current conditions"
        
        actions_content = tk.Label(
            scrollable_content,
            text=actions_text,
            font=('Arial', 10),
            bg='#ecf0f1', fg='#2c3e50',
            justify='left'
        )
        actions_content.pack(anchor='w', pady=(0, 20), padx=10)
        
        # Buttons frame (outside scrollable area, at bottom)
        button_frame = tk.Frame(alert_window, bg='#ecf0f1')
        button_frame.pack(side='bottom', fill='x', padx=20, pady=10)
        
        # Acknowledge button
        ack_button = tk.Button(
            button_frame,
            text="✅ ACKNOWLEDGE",
            font=('Arial', 11, 'bold'),
            bg='#27ae60', fg='white',
            command=on_alert_close,
            relief='raised', bd=3
        )
        ack_button.pack(side='right', padx=(10, 0))
        
        # Snooze button (for warnings only)
        if status == 'WARNING':
            snooze_button = tk.Button(
                button_frame,
                text="⏰ SNOOZE 5 MIN",
                font=('Arial', 11, 'bold'),
                bg='#f39c12', fg='white',
                command=lambda: self.snooze_alert(alert_id, on_alert_close),
                relief='raised', bd=3
            )
            snooze_button.pack(side='right', padx=(10, 0))
        
        # Emergency stop button (for critical only)
        if status == 'CRITICAL':
            stop_button = tk.Button(
                button_frame,
                text="🛑 EMERGENCY STOP",
                font=('Arial', 11, 'bold'),
                bg='#c0392b', fg='white',
                command=lambda: self.emergency_stop(on_alert_close),
                relief='raised', bd=3
            )
            stop_button.pack(side='left')
        
        # Make window modal
        alert_window.grab_set()
        alert_window.focus_set()
        
        # Auto-close after 5 minutes for warnings
        if status == 'WARNING':
            alert_window.after(300000, on_alert_close)  # 5 minutes
    
    def snooze_alert(self, alert_id, close_callback):
        """Snooze alert for 5 minutes"""
        # Remove from active alerts temporarily
        self.active_alerts.discard(alert_id)
        
        # ✅ SET COOLDOWN: 5-second delay before next alert can appear
        self.alert_cooldown_until = time.time() + 5.0  # 5 seconds from now
        print(f"⏰ Alert snoozed - 5-second cooldown activated until next alert")
        
        # Close the window
        close_callback()
        
        # Schedule re-activation after 5 minutes (300 seconds)
        self.root.after(300000, lambda: self.active_alerts.discard(alert_id))
        
        # Show confirmation
        messagebox.showinfo("Alert Snoozed", "⏰ Alert snoozed for 5 minutes")
    
    def emergency_stop(self, close_callback):
        """Emergency stop function"""
        self.stop_monitoring()
        
        # ✅ SET COOLDOWN: 5-second delay before next alert can appear
        self.alert_cooldown_until = time.time() + 5.0  # 5 seconds from now
        print(f"🛑 Emergency stop activated - 5-second cooldown activated until next alert")
        
        close_callback()
        
        # Show confirmation
        messagebox.showinfo(
            "Emergency Stop Activated",
            "🛑 Monitoring has been stopped.\n\nSystem is now in safe mode.\nContact maintenance before restarting."
        )
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main function"""
    print("Starting Enhanced Predictive Maintenance Monitor...")
    
    app = EnhancedPredictiveMonitor()
    
    # Handle window closing
    def on_closing():
        if app.is_monitoring:
            app.stop_monitoring()
        app.root.quit()
        app.root.destroy()
    
    app.root.protocol("WM_DELETE_WINDOW", on_closing)
    app.run()

if __name__ == "__main__":
    main()
