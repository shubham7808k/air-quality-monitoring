from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import logging
import os
import json
import numpy as np
from backend.database_models import DatabaseManager
from backend.aqi_calculation import AQICalculator
from backend.spatial_mapping import SpatialAQIMapper
from config import SENSOR_NODES, AQI_CATEGORIES
import pandas as pd
from backend.arduino_reader import arduino_reader
import threading
import time
from backend.data_collection import SensorDataCollector
from flask import request, jsonify
from backend.arduino_aqi import process_sensor_data

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Arduino sensor status API
@app.route("/api/arduino/status", methods=["GET"])
def arduino_status():
    return jsonify(arduino_reader.snapshot())

# Initialize managers
db = DatabaseManager()
aqi_calc = AQICalculator()
mapper = SpatialAQIMapper()

# Automatic simulated sensor data updates
collector = SensorDataCollector()

def update_sensor_data():
    """Generate new simulated readings and calculate AQI."""
    while True:
        try:
            collector.collect_all_sensors(use_simulation=True)

            latest_readings = db.get_latest_reading_all_nodes()

            for reading in latest_readings:
                reading_dict = {
                    "pm25": reading.pm25,
                    "pm10": reading.pm10,
                    "no2": reading.no2 or 0,
                    "co": reading.co or 0,
                    "temperature": reading.temperature,
                    "humidity": reading.humidity,
                    "timestamp": reading.timestamp
                }

                result = aqi_calc.calculate_aqi(reading_dict)

                db.add_aqi_value({
                    "node_id": reading.node_id,
                    "timestamp": reading.timestamp,
                    "aqi_value": result["value"],
                    "aqi_category": result["category"],
                    "dominant_pollutant": result["dominant_pollutant"],
                    "color_code": result["color"]
                })

            logger.info("AirSense sensor readings and AQI updated.")

        except Exception:
            logger.exception("Automatic sensor update failed")

        time.sleep(60)

# ============= calculated aqi function =============

@app.route("/api/arduino/aqi")
def arduino_aqi_api():
    from flask import jsonify

    # Reuse the existing Arduino status route.
    status_response = app.make_response(
        app.view_functions["arduino_status"]()
    )

    if status_response.status_code >= 400:
        return jsonify({
            "error": "Unable to retrieve Arduino readings"
        }), 502

    try:
        sensor_data = status_response.get_json()
    except Exception:
        return jsonify({
            "error": "Invalid Arduino status response"
        }), 502

    if not isinstance(sensor_data, dict):
        return jsonify({"error": "Invalid sensor data"}), 502

    latest = sensor_data.get("latest") or {}

    latest["connected"] = sensor_data.get("connected", False)

    result = process_sensor_data(latest)

    return jsonify(result)


# ============= HELPER FUNCTIONS =============

def get_aqi_color(aqi_value):
    """Get color code from AQI value"""
    for cat_name, (cat_low, cat_high, color) in AQI_CATEGORIES.items():
        if cat_low <= aqi_value <= cat_high:
            return color
    return '#4A148C'

def get_aqi_category(aqi_value):
    """Get category from AQI value"""
    for cat_name, (cat_low, cat_high, _) in AQI_CATEGORIES.items():
        if cat_low <= aqi_value <= cat_high:
            return cat_name
    return 'Severe'

# ============= API ENDPOINTS =============

@app.route('/')
def index():
    """Serve main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get all data for dashboard"""
    try:
        latest_readings = db.get_latest_reading_all_nodes()
        latest_aqi = db.get_latest_aqi_all_nodes()
        
        dashboard_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sensors': [],
            'overall_status': {},
            'alerts': [],
            'arduino': arduino_reader.snapshot()
            }

        
        aqi_values = []
        
        # Process each sensor
        for aqi_record in latest_aqi:
            node_config = SENSOR_NODES.get(aqi_record.node_id, {})
            
            # Find corresponding reading
            reading = next((r for r in latest_readings if r.node_id == aqi_record.node_id), None)
            
            sensor_info = {
                'node_id': aqi_record.node_id,
                'name': node_config.get('name', 'Unknown'),
                'location_type': node_config.get('location_type', 'general'),
                'latitude': node_config.get('latitude', 0),
                'longitude': node_config.get('longitude', 0),
                'timestamp': aqi_record.timestamp.isoformat(),
                'measurements': {},
                'aqi': {
                    'value': round(aqi_record.aqi_value, 1),
                    'category': aqi_record.aqi_category,
                    'color': get_aqi_color(aqi_record.aqi_value),
                    'dominant_pollutant': aqi_record.dominant_pollutant
                }
            }
            
            if reading:
                sensor_info['measurements'] = {
                    'pm25': round(reading.pm25, 2),
                    'pm10': round(reading.pm10, 2),
                    'no2': round(reading.no2 if reading.no2 else 0, 2),
                    'co': round(reading.co if reading.co else 0, 2),
                    'temperature': round(reading.temperature, 1),
                    'humidity': round(reading.humidity, 1)
                }
            
            dashboard_data['sensors'].append(sensor_info)
            aqi_values.append(aqi_record.aqi_value)
        
        # Overall status
        if aqi_values:
            avg_aqi = np.mean(aqi_values)
            max_aqi = np.max(aqi_values)
            
            worst_node_idx = np.argmax(aqi_values)
            worst_node = latest_aqi[worst_node_idx]
            worst_node_name = SENSOR_NODES.get(worst_node.node_id, {}).get('name', 'Unknown')
            
            dashboard_data['overall_status'] = {
                'avg_aqi': round(avg_aqi, 1),
                'max_aqi': round(max_aqi, 1),
                'min_aqi': round(np.min(aqi_values), 1),
                'worst_location': worst_node_name,
                'worst_aqi': round(max_aqi, 1),
                'status_category': get_aqi_category(avg_aqi),
                'status_color': get_aqi_color(avg_aqi)
            }
            
            # Generate alerts
            for aqi_record in latest_aqi:
                if aqi_record.aqi_value > 200:
                    node_name = SENSOR_NODES.get(aqi_record.node_id, {}).get('name', 'Unknown')
                    severity = 'critical' if aqi_record.aqi_value > 300 else 'high'
                    
                    dashboard_data['alerts'].append({
                        'severity': severity,
                        'message': f"⚠️ {node_name}: AQI {aqi_record.aqi_value:.0f} - {aqi_record.aqi_category}",
                        'location': node_name,
                        'aqi': round(aqi_record.aqi_value, 1)
                    })
        
        return jsonify(dashboard_data), 200
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor/<node_id>/24h', methods=['GET'])
def get_sensor_24h(node_id):
    """Get last 24 hours of data for a sensor"""
    try:
        readings = db.get_last_24h_readings(node_id)
        
        if not readings:
            return jsonify({'message': 'No data available'}), 404
        
        data = []
        for reading in readings:
            data.append({
                'timestamp': reading.timestamp.isoformat(),
                'pm25': round(reading.pm25, 2),
                'pm10': round(reading.pm10, 2),
                'temperature': round(reading.temperature, 1),
                'humidity': round(reading.humidity, 1)
            })
        
        node_config = SENSOR_NODES.get(node_id, {})
        
        return jsonify({
            'node_id': node_id,
            'name': node_config.get('name', 'Unknown'),
            'data': data,
            'count': len(data)
        }), 200
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/aqi/<node_id>/24h', methods=['GET'])
def get_aqi_24h(node_id):
    """Get AQI history for last 24 hours"""
    try:
        aqi_history = db.get_aqi_24h_history(node_id)
        
        if not aqi_history:
            return jsonify({'message': 'No data available'}), 404
        
        data = []
        for aqi_record in aqi_history:
            data.append({
                'timestamp': aqi_record.timestamp.isoformat(),
                'aqi': round(aqi_record.aqi_value, 1),
                'category': aqi_record.aqi_category,
                'color': get_aqi_color(aqi_record.aqi_value)
            })
        
        node_config = SENSOR_NODES.get(node_id, {})
        
        return jsonify({
            'node_id': node_id,
            'name': node_config.get('name', 'Unknown'),
            'data': data,
            'count': len(data)
        }), 200
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Return historical readings and AQI for the Analytics popup."""
    try:
        node_id = request.args.get('node_id', '').strip()

        if not node_id:
            return jsonify({
                'success': False,
                'error': 'Please provide a sensor node_id'
            }), 400

        # Retrieve real historical data from the existing database.
        readings = db.get_last_24h_readings(node_id)
        aqi_history = db.get_aqi_24h_history(node_id)

        # Format database objects as JSON-compatible dictionaries.
        readings_data = []
        for reading in readings or []:
            readings_data.append({
                'timestamp': reading.timestamp.isoformat(),
                'pm25': float(reading.pm25 or 0),
                'pm10': float(reading.pm10 or 0),
                'temperature': float(reading.temperature or 0),
                'humidity': float(reading.humidity or 0)
            })

        aqi_data = []
        for record in aqi_history or []:
            aqi_data.append({
                'timestamp': record.timestamp.isoformat(),
                'aqi': float(record.aqi_value),
                'category': record.aqi_category,
                'color': get_aqi_color(record.aqi_value)
            })

        return jsonify({
            'success': True,
            'node_id': node_id,
            'readings': readings_data,
            'aqi_history': aqi_data
        }), 200

    except Exception as e:
        logger.exception('Analytics API failed')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    
@app.route("/api/aqi/sub-indices", methods=["POST"])
def aqi_sub_indices():
    """Calculate particulate sub-indices from supplied concentrations."""
    data = request.get_json(silent=True) or {}

    if "pm25" not in data or "pm10" not in data:
        return jsonify({
            "success": False,
            "message": "Provide pm25 and pm10 concentrations in µg/m³."
        }), 400

    result = calculate_particle_sub_indices(
        pm25=data["pm25"],
        pm10=data["pm10"]
    )

    if (
        result["pm25_sub_index"] is None
        or result["pm10_sub_index"] is None
    ):
        return jsonify({
            "success": False,
            "message": "Concentrations must be valid, non-negative numbers."
        }), 400

    return jsonify({
        "success": True,
        "pm25_sub_index": result["pm25_sub_index"],
        "pm10_sub_index": result["pm10_sub_index"],
        "overall_aqi": None,
        "status": "Experimental particulate sub-indices only"
    })


# ============= HISTORICAL ALERTS API =============

@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """Return saved AQI history for all sensors from the last 24 hours."""
    try:
        alerts = []

        for node_id, sensor_info in SENSOR_NODES.items():
            records = db.get_aqi_24h_history(node_id) or []
            sensor_name = sensor_info.get('name', node_id)

            for record in records:
                aqi = float(record.aqi_value or 0)

                # Classify the AQI without excluding normal records.
                if aqi > 300:
                    severity = 'critical'
                elif aqi > 200:
                    severity = 'high'
                else:
                    severity = 'normal'

                alerts.append({
                    'node_id': node_id,
                    'sensor_name': sensor_name,
                    'timestamp': (
                        record.timestamp.isoformat()
                        if record.timestamp else None
                    ),
                    'aqi': round(aqi, 1),
                    'category': record.aqi_category,
                    'severity': severity,
                    'dominant_pollutant': getattr(
                        record, 'dominant_pollutant', None
                    ),
                    'message': (
                        f'{sensor_name}: AQI {aqi:.1f} '
                        f'- {record.aqi_category}'
                    )
                })

        # Newest records first.
        alerts.sort(
            key=lambda item: item['timestamp'] or '',
            reverse=True
        )

        return jsonify({
            'success': True,
            'count': len(alerts),
            'alerts': alerts
        }), 200

    except Exception as e:
        logger.exception('Historical AQI API failed')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get statistical summary"""
    try:
        stats = db.get_database_stats()
        
        latest_aqi = db.get_latest_aqi_all_nodes()
        aqi_values = [aqi.aqi_value for aqi in latest_aqi]
        
        if aqi_values:
            summary = {
                'database': stats,
                'aqi': {
                    'average': round(np.mean(aqi_values), 1),
                    'median': round(np.median(aqi_values), 1),
                    'std': round(np.std(aqi_values), 1),
                    'min': round(np.min(aqi_values), 1),
                    'max': round(np.max(aqi_values), 1)
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        else:
            summary = {'error': 'No data available'}
        
        return jsonify(summary), 200
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get list of all sensor nodes"""
    try:
        nodes = []
        for node_id, config in SENSOR_NODES.items():
            nodes.append({
                'node_id': node_id,
                'name': config.get('name'),
                'latitude': config.get('latitude'),
                'longitude': config.get('longitude'),
                'location_type': config.get('location_type'),
                'description': config.get('description')
            })
        
        return jsonify(nodes), 200
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmap', methods=['GET'])
def get_heatmap_data():
    """Get heatmap data"""
    try:
        latest_aqi = db.get_latest_aqi_all_nodes()
        
        heatmap_data = []
        for aqi_record in latest_aqi:
            node_config = SENSOR_NODES.get(aqi_record.node_id, {})
            heatmap_data.append({
                'lat': node_config.get('latitude', 0),
                'lon': node_config.get('longitude', 0),
                'aqi': aqi_record.aqi_value,
                'name': node_config.get('name', 'Unknown'),
                'color': get_aqi_color(aqi_record.aqi_value)
            })
        
        return jsonify(heatmap_data), 200
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Server error'}), 500


@app.route("/api/arduino/latest")
def arduino_latest():
    arduino_reader.start()
    return jsonify(arduino_reader.snapshot())


@app.route("/api/arduino/history")
def arduino_history():
    try:
        arduino_reader.start()

        history = arduino_reader.get_history()

        if history is None:
            history = []

        return jsonify({
            "success": True,
            "count": len(history),
            "history": history
        })

    except Exception:
        app.logger.exception("Failed to load Arduino history")
        return jsonify({
            "success": False,
            "error": "Unable to retrieve Arduino history"
        }), 500


@app.route("/api/arduino/experimental-index")
def arduino_experimental_index():
    try:
        # Reuse the existing Arduino status endpoint.
        status_response = app.make_response(
            app.view_functions["arduino_status"]()
        )

        data = status_response.get_json(silent=True)

        if status_response.status_code >= 400 or not isinstance(data, dict):
            return jsonify({
                "error": "Unable to retrieve Arduino sensor readings"
            }), 502

        latest = data.get("latest") or {}
        result = process_sensor_data(latest)

        result["connected"] = bool(data.get("connected", False))
        result["timestamp"] = latest.get("timestamp")

        return jsonify(result)

    except Exception:
        app.logger.exception("Experimental sensor index failed")
        return jsonify({
            "error": "Unable to calculate experimental index"
        }), 500


# ============= MAIN =============

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("STARTING FLASK WEB DASHBOARD")
    print("=" * 70)
    print("\n✓ Dashboard running at: http://localhost:5000")
    print("✓ API available at: http://localhost:5000/api/*")
    print("✓ Automatic sensor updates: every 60 seconds")
    print("\nPress Ctrl+C to stop\n")

    # Start Arduino USB sensor reader
    arduino_reader.start()
    print("✓ Arduino sensor reader started")

    # Start automatic sensor updates in the background
    updater = threading.Thread(
        target=update_sensor_data,
        daemon=True
    )
    updater.start()

    # Disable Flask's reloader to prevent duplicate updater threads
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )
