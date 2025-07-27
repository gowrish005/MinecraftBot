from flask import render_template, jsonify, request, redirect, url_for, flash
from views import dashboard_view, machine_view
from controllers import get_process_data, get_machine_data, update_machine_status, register_user, authenticate_user, logout_user, login_required
import datetime

def register_routes(app):
    """Register all application routes"""
    
    # Web UI routes
    @app.route('/')
    @login_required
    def index():
        """Main dashboard page"""
        return dashboard_view()
    
    @app.route('/machine/<process_name>/<machine_id>')
    def machine_detail(process_name, machine_id):
        """Machine detail view"""
        return machine_view(process_name, machine_id)
        
    # User authentication routes
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            success, message = register_user(email, password)
            if success:
                flash(message, 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            success, message = authenticate_user(email, password)
            if success:
                flash(message, 'success')
                return redirect(url_for('index'))
            else:
                flash(message, 'danger')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        logout_user()
        flash('Logged out successfully.', 'info')
        return redirect(url_for('login'))

    # AI Prediction endpoint
    @app.route('/predict', methods=['POST'])
    def predict():
        """AI prediction endpoint for machine health analysis"""
        try:
            data = request.get_json()
            
            if not data or 'sensor_data' not in data:
                return jsonify({'error': 'No sensor data provided'}), 400
                
            sensor_data = data['sensor_data']
            
            # Basic validation - expect sequence of 15 data points with 6 parameters each
            if not isinstance(sensor_data, list) or len(sensor_data) == 0:
                return jsonify({'error': 'Invalid sensor data format'}), 400
                
            # Get the latest sensor values (last item in the sequence)
            if isinstance(sensor_data[0], list) and len(sensor_data[0]) == 6:
                latest_values = sensor_data[-1]
            else:
                return jsonify({'error': 'Invalid sensor data structure'}), 400
                
            # Extract individual parameters
            temp = latest_values[0]
            humidity = latest_values[1] 
            airflow = latest_values[2]
            fan_speed = latest_values[3]
            heating_power = latest_values[4]
            fan_power = latest_values[5]
            
            # Heuristic health analysis (fallback when AI model is not available)
            health_score = 1.0
            issues = []
            
            # Temperature analysis (optimal: 22-32°C)
            if temp < 20 or temp > 35:
                health_score -= 0.25
                issues.append(f'Temperature ({temp:.1f}°C) outside optimal range')
            elif temp < 22 or temp > 32:
                health_score -= 0.1
                issues.append(f'Temperature ({temp:.1f}°C) suboptimal')
                
            # Humidity analysis (optimal: 45-75%)
            if humidity < 35 or humidity > 85:
                health_score -= 0.25
                issues.append(f'Humidity ({humidity:.1f}%) critically high/low')
            elif humidity < 45 or humidity > 75:
                health_score -= 0.1
                issues.append(f'Humidity ({humidity:.1f}%) suboptimal')
                
            # Airflow analysis (optimal: 90-140 CFM)
            if airflow < 70 or airflow > 160:
                health_score -= 0.2
                issues.append(f'Airflow ({airflow:.1f} CFM) critically low/high')
            elif airflow < 90 or airflow > 140:
                health_score -= 0.1
                issues.append(f'Airflow ({airflow:.1f} CFM) suboptimal')
                
            # Fan speed analysis (optimal: 1900-2350 RPM)
            if fan_speed < 1600 or fan_speed > 2700:
                health_score -= 0.15
                issues.append(f'Fan speed ({fan_speed} RPM) critically low/high')
            elif fan_speed < 1900 or fan_speed > 2350:
                health_score -= 0.08
                issues.append(f'Fan speed ({fan_speed} RPM) suboptimal')
                
            # Heating power analysis (optimal: 13-17 kW)
            if heating_power < 10 or heating_power > 20:
                health_score -= 0.15
                issues.append(f'Heating power ({heating_power:.1f} kW) critically low/high')
            elif heating_power < 13 or heating_power > 17:
                health_score -= 0.08
                issues.append(f'Heating power ({heating_power:.1f} kW) suboptimal')
                
            # Fan power analysis (optimal: 190-260 W)
            if fan_power < 150 or fan_power > 300:
                health_score -= 0.15
                issues.append(f'Fan power ({fan_power:.1f} W) critically low/high')
            elif fan_power < 190 or fan_power > 260:
                health_score -= 0.08
                issues.append(f'Fan power ({fan_power:.1f} W) suboptimal')
                
            # Ensure health score doesn't go below 0
            health_score = max(0.0, health_score)
            
            # Determine status and confidence
            if health_score > 0.8:
                status = 'HEALTHY'
                confidence = 0.85 + (health_score - 0.8) * 0.75  # 0.85-0.95
            elif health_score > 0.6:
                status = 'WARNING' 
                confidence = 0.70 + (health_score - 0.6) * 0.75  # 0.70-0.85
            else:
                status = 'CRITICAL'
                confidence = 0.60 + health_score * 0.25  # 0.60-0.75
                
            # Estimate time to failure based on health score
            if health_score > 0.8:
                time_to_failure = 40 + (health_score - 0.8) * 100  # 40-60 hours
            elif health_score > 0.6:
                time_to_failure = 15 + (health_score - 0.6) * 125  # 15-40 hours  
            else:
                time_to_failure = 2 + health_score * 21.67  # 2-15 hours
                
            # Add some realistic variation
            import random
            confidence += random.uniform(-0.05, 0.05)
            time_to_failure += random.uniform(-5, 5)
            
            # Ensure values are in valid ranges
            confidence = max(0.5, min(0.99, confidence))
            time_to_failure = max(1.0, time_to_failure)
            
            response = {
                'predicted_status': status,
                'confidence': confidence,
                'health_score': health_score,
                'time_to_failure': time_to_failure,
                'issues': issues,
                'analysis': {
                    'temperature': {'value': temp, 'status': 'optimal' if 22 <= temp <= 32 else 'warning' if 20 <= temp <= 35 else 'critical'},
                    'humidity': {'value': humidity, 'status': 'optimal' if 45 <= humidity <= 75 else 'warning' if 35 <= humidity <= 85 else 'critical'},
                    'airflow': {'value': airflow, 'status': 'optimal' if 90 <= airflow <= 140 else 'warning' if 70 <= airflow <= 160 else 'critical'},
                    'fan_speed': {'value': fan_speed, 'status': 'optimal' if 1900 <= fan_speed <= 2350 else 'warning' if 1600 <= fan_speed <= 2700 else 'critical'},
                    'heating_power': {'value': heating_power, 'status': 'optimal' if 13 <= heating_power <= 17 else 'warning' if 10 <= heating_power <= 20 else 'critical'},
                    'fan_power': {'value': fan_power, 'status': 'optimal' if 190 <= fan_power <= 260 else 'warning' if 150 <= fan_power <= 300 else 'critical'}
                }
            }
            
            return jsonify(response)
            
        except Exception as e:
            print(f"Error in predict endpoint: {str(e)}")
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    # Alert management endpoints  
    @app.route('/acknowledge_alert', methods=['POST'])
    def acknowledge_alert():
        """Acknowledge an alert"""
        try:
            data = request.get_json()
            alert_id = data.get('alertId')
            
            # Log the acknowledgment
            print(f"Alert acknowledged: {alert_id}")
            
            # Here you could store the acknowledgment in database if needed
            # For now, just return success
            return jsonify({'status': 'success', 'message': 'Alert acknowledged', 'alertId': alert_id})
            
        except Exception as e:
            print(f"Error acknowledging alert: {str(e)}")
            return jsonify({'error': 'Failed to acknowledge alert'}), 500

    @app.route('/emergency_stop', methods=['POST'])
    def emergency_stop():
        """Emergency stop endpoint"""
        try:
            data = request.get_json()
            alert_id = data.get('alertId')
            timestamp = data.get('timestamp')
            
            # Log the emergency stop
            print(f"🛑 EMERGENCY STOP REQUESTED - Alert: {alert_id}, Time: {timestamp}")
            
            # Here you could implement actual emergency stop logic
            # For now, just log and return success
            return jsonify({
                'status': 'success', 
                'message': 'Emergency stop initiated',
                'alertId': alert_id,
                'timestamp': timestamp
            })
            
        except Exception as e:
            print(f"Error processing emergency stop: {str(e)}")
            return jsonify({'error': 'Failed to process emergency stop'}), 500
        
    # API routes
    @app.route('/api/process-data', methods=['GET'])
    def process_data():
        """Get data for all processes"""
        print("API endpoint /api/process-data called")
        from pymongo import MongoClient
        from flask import g
        
        try:
            # Create a dedicated connection for this API call
            mongo_client = MongoClient(app.config['MONGO_URI'])
            db = mongo_client.get_database()
            print("MongoDB connection established")
            
            # Make db available to the get_process_data function
            g.db = db
            
            try:
                data = get_process_data()
                print(f"API returned data: {type(data)} with {len(data) if isinstance(data, list) else 'ERROR'} items")
                return jsonify(data)
            except Exception as e:
                print(f"Error in process_data API when getting data: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": str(e)}), 500
            finally:
                # Always close the connection
                mongo_client.close()
                print("MongoDB connection closed")
        except Exception as e:
            print(f"Error in process_data API when connecting to MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"MongoDB connection error: {str(e)}"}), 500
    
    @app.route('/api/process/<process_name>', methods=['GET'])
    def process_detail(process_name):
        """Get data for a specific process"""
        from pymongo import MongoClient
        from flask import g
        
        # Create a dedicated connection for this API call
        mongo_client = MongoClient(app.config['MONGO_URI'])
        db = mongo_client.get_database()
        
        # Make db available to the get_process_data function
        g.db = db
        
        try:
            data = get_process_data(process_name)
            return jsonify(data)
        finally:
            # Always close the connection
            mongo_client.close()
    
    # New endpoint for machine status
    @app.route('/api/machine/<machine_id>/status', methods=['GET'])
    def machine_status(machine_id):
        """Get status and data for a specific machine"""
        return jsonify(get_machine_data(machine_id))
    
    # New endpoint for machine readings with time range filter
    @app.route('/api/machine/<machine_id>/readings', methods=['GET'])
    def machine_readings(machine_id):
        """Get readings for a specific machine with optional time range"""
        # Get time range from query parameters
        time_range = request.args.get('range', '24h')  # Default to 24 hours
        
        # Get machine data
        machine_data = get_machine_data(machine_id)
        
        # Filter readings based on time range
        if 'readings' in machine_data:
            current_time = datetime.datetime.utcnow()
            
            # Calculate time delta based on range parameter
            if time_range == '1h':
                delta = datetime.timedelta(hours=1)
            elif time_range == '6h':
                delta = datetime.timedelta(hours=6)
            else:  # Default to 24h
                delta = datetime.timedelta(hours=24)
            
            # Filter readings
            cutoff_time = current_time - delta
            filtered_readings = [
                r for r in machine_data['readings'] 
                if datetime.datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')) > cutoff_time
            ]
            
            machine_data['readings'] = filtered_readings
        
        return jsonify(machine_data)
    
    # New endpoint for machine control
    @app.route('/api/machine/<machine_id>/control', methods=['POST'])
    def machine_control(machine_id):
        """Control a machine (start, stop, maintenance, etc.)"""
        if not request.json or 'action' not in request.json:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
        action = request.json['action']
        timestamp = datetime.datetime.utcnow().isoformat()
        
        # Map actions to statuses
        status_map = {
            'start': 'running',
            'pause': 'idle',
            'maintenance': 'maintenance',
            'emergency-stop': 'error'
        }
        
        # Validate action
        if action not in status_map:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        # Update machine status
        result = update_machine_status(machine_id, {
            'status': status_map[action],
            'timestamp': timestamp
        })
        
        return jsonify(result)
    
    # Add health check endpoint for Render.com
    @app.route('/health')
    def health_check():
        """Health check endpoint for Render.com"""
        try:
            # Try to get a database connection to verify everything is working
            from models import get_db
            from flask import g
            
            try:
                db = get_db()
                # Just ping the database
                db.command('ping')
                status = "healthy"
                db_status = "connected"
            except Exception as e:
                status = "degraded"
                db_status = f"error: {str(e)}"
            finally:
                # Close the connection if it exists
                if hasattr(g, 'mongo_client'):
                    g.mongo_client.close()
                    
            # Return health status
            from flask import jsonify
            return jsonify({
                "status": status,
                "database": db_status,
                "timestamp": str(datetime.datetime.now())
            })
        except Exception:
            from flask import jsonify
            return jsonify({
                "status": "unhealthy", 
                "database": "unavailable",
                "timestamp": str(datetime.datetime.now())
            }), 500