"""
Flask Web Dashboard for Air Quality Monitoring System
Provides real-time visualization of AQI data
"""

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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize managers
db = DatabaseManager()
aqi_calc = AQICalculator()
mapper = SpatialAQIMapper()

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
            'alerts': []
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

# ============= MAIN =============

if __name__ == '__main__':
    print("\n" + "="*70)
    print("STARTING FLASK WEB DASHBOARD")
    print("="*70)
    print("\n✓ Dashboard running at: http://localhost:5000")
    print("✓ API available at: http://localhost:5000/api/*")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)