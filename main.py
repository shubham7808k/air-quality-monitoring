from backend.data_collection import SensorDataCollector
from backend.database_models import DatabaseManager
from backend.aqi_calculation import AQICalculator
from backend.spatial_mapping import SpatialAQIMapper
from backend.calibration_models import SensorCalibration
from backend.prediction_models import SimpleAQIPredictor
from config import SENSOR_NODES
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import logging
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AirQualityMonitoringSystem:
    """Complete Air Quality Monitoring System"""
    
    def __init__(self):
        print("\n" + "="*70)
        print("INITIALIZING AIR QUALITY MONITORING SYSTEM")
        print("="*70 + "\n")
        
        try:
            self.collector = SensorDataCollector()
            print("✓ Data Collector initialized")
            
            self.db = DatabaseManager()
            print("✓ Database Manager initialized")
            
            self.aqi_calc = AQICalculator()
            print("✓ AQI Calculator initialized")
            
            self.mapper = SpatialAQIMapper()
            print("✓ Spatial Mapper initialized")
            
            self.calibrator = SensorCalibration()
            print("✓ Calibration Model initialized")
            
            self.predictor = SimpleAQIPredictor()
            print("✓ Prediction Model initialized")
            
            print("\n✓ System initialized successfully!\n")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise
    
    def collect_24h_data(self):
        """Collect simulated data for last 24 hours"""
        print("\n" + "="*70)
        print("STEP 1: COLLECTING 24-HOUR SIMULATION DATA")
        print("="*70 + "\n")
        
        try:
            print("Collecting data for 24 hours (simulating hourly readings)...\n")
            self.collector.collect_multiple_intervals(24)
            
            stats = self.db.get_database_stats()
            
            print(f"\n✓ Simulation Complete!")
            print(f"  Total readings in last 24h: {stats.get('readings_24h', 0)}")
            print(f"  Active sensor nodes: {stats.get('active_nodes', 0)}")
            print(f"  Total readings in DB: {stats.get('total_readings', 0)}\n")
            
            return True
        except Exception as e:
            logger.error(f"Error collecting data: {e}")
            return False
    
    def calculate_aqi_for_all(self):
        """Calculate AQI for all latest readings"""
        print("="*70)
        print("STEP 2: CALCULATING AQI VALUES")
        print("="*70 + "\n")
        
        try:
            latest_readings = self.db.get_latest_reading_all_nodes()
            print(f"Found {len(latest_readings)} latest readings\n")
            
            aqi_results = []
            
            for reading in latest_readings:
                reading_dict = {
                    'pm25': reading.pm25,
                    'pm10': reading.pm10,
                    'no2': reading.no2 if reading.no2 else 0,
                    'co': reading.co if reading.co else 0,
                    'temperature': reading.temperature,
                    'humidity': reading.humidity,
                    'timestamp': reading.timestamp
                }
                
                aqi = self.aqi_calc.calculate_aqi(reading_dict)
                
                # Store in database
                aqi_dict = {
                    'node_id': reading.node_id,
                    'timestamp': reading.timestamp,
                    'aqi_value': aqi['value'],
                    'aqi_category': aqi['category'],
                    'dominant_pollutant': aqi['dominant_pollutant'],
                    'color_code': aqi['color']
                }
                
                self.db.add_aqi_value(aqi_dict)
                aqi_results.append({
                    'node_id': reading.node_id,
                    'aqi': aqi['value'],
                    'category': aqi['category'],
                    'color': aqi['color'],
                    'dominant_pollutant': aqi['dominant_pollutant']
                })
                
                node_name = SENSOR_NODES.get(reading.node_id, {}).get('name', reading.node_id)
                advisory = self.aqi_calc.get_health_advisory(aqi['category'])
                
                print(f"  {node_name}:")
                print(f"    AQI: {aqi['value']:.1f} ({aqi['category']})")
                print(f"    Advisory: {advisory['general']}")
                print()
            
            return aqi_results
        except Exception as e:
            logger.error(f"Error calculating AQI: {e}")
            return []
    
    def generate_heatmap(self):
        """Generate spatial heatmap"""
        print("="*70)
        print("STEP 3: GENERATING SPATIAL HEATMAP")
        print("="*70 + "\n")
        
        try:
            latest_aqi = self.db.get_latest_aqi_all_nodes()
            aqi_data_list = []
            
            for aqi_record in latest_aqi:
                node_config = SENSOR_NODES.get(aqi_record.node_id, {})
                aqi_data_list.append({
                    'lat': node_config.get('latitude', 0),
                    'lon': node_config.get('longitude', 0),
                    'aqi': aqi_record.aqi_value,
                    'name': node_config.get('name', aqi_record.node_id)
                })
            
            if len(aqi_data_list) > 0:
                aqi_df = pd.DataFrame(aqi_data_list)
                
                # Create static directory if not exists
                os.makedirs('static', exist_ok=True)
                
                self.mapper.create_folium_heatmap(aqi_df, 'static/heatmap.html')
                print(f"✓ Heatmap generated at: static/heatmap.html")
                print(f"  Sensor locations covered: {len(aqi_df)}")
                print()
                
                return True
            else:
                print("⚠️  No AQI data available for heatmap\n")
                return False
        except Exception as e:
            logger.error(f"Error generating heatmap: {e}")
            return False
    
    def display_summary(self):
        """Display system summary"""
        print("="*70)
        print("STEP 4: SYSTEM SUMMARY")
        print("="*70 + "\n")
        
        try:
            stats = self.db.get_database_stats()
            
            print("Database Statistics:")
            print(f"  Total readings: {stats.get('total_readings', 0)}")
            print(f"  Readings in last 24h: {stats.get('readings_24h', 0)}")
            print(f"  AQI records: {stats.get('total_aqi', 0)}")
            print(f"  Active sensor nodes: {stats.get('active_nodes', 0)}\n")
            
            latest_aqi = self.db.get_latest_aqi_all_nodes()
            
            if len(latest_aqi) > 0:
                aqi_values = [aqi.aqi_value for aqi in latest_aqi]
                
                print("Current AQI Status Across Campus:")
                print(f"  Average AQI: {np.mean(aqi_values):.1f}")
                print(f"  Maximum AQI: {np.max(aqi_values):.1f}")
                print(f"  Minimum AQI: {np.min(aqi_values):.1f}\n")
                
                print("Sensor-wise Current AQI:")
                for aqi_record in latest_aqi:
                    node_name = SENSOR_NODES.get(aqi_record.node_id, {}).get('name', aqi_record.node_id)
                    print(f"  {node_name}: {aqi_record.aqi_value:.1f} ({aqi_record.aqi_category})")
                
                print()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
    
    def display_node_details(self, node_id):
        """Display details for specific node"""
        print("\n" + "="*70)
        print(f"DETAILED NODE INFORMATION: {node_id}")
        print("="*70 + "\n")
        
        try:
            node_config = SENSOR_NODES.get(node_id, {})
            print(f"Node Name: {node_config.get('name', 'Unknown')}")
            print(f"Location Type: {node_config.get('location_type', 'Unknown')}")
            print(f"Description: {node_config.get('description', 'N/A')}")
            print(f"Coordinates: ({node_config.get('latitude', 0)}, {node_config.get('longitude', 0)})\n")
            
            # Get readings
            readings = self.db.get_last_24h_readings(node_id)
            
            if readings:
                print(f"Sensor Readings (last 24h): {len(readings)} records\n")
                
                latest = readings[-1]
                print("Latest Reading:")
                print(f"  Timestamp: {latest.timestamp}")
                print(f"  PM2.5: {latest.pm25:.2f} µg/m³")
                print(f"  PM10: {latest.pm10:.2f} µg/m³")
                print(f"  NO2: {latest.no2:.2f} ppb" if latest.no2 else "  NO2: N/A")
                print(f"  CO: {latest.co:.2f} ppm" if latest.co else "  CO: N/A")
                print(f"  Temperature: {latest.temperature:.1f}°C")
                print(f"  Humidity: {latest.humidity:.1f}%")
                print(f"  Calibrated: {latest.is_calibrated}\n")
                
                # Statistics
                pm25_values = [r.pm25 for r in readings]
                print("PM2.5 Statistics (24h):")
                print(f"  Average: {np.mean(pm25_values):.2f} µg/m³")
                print(f"  Max: {np.max(pm25_values):.2f} µg/m³")
                print(f"  Min: {np.min(pm25_values):.2f} µg/m³")
                print(f"  Std Dev: {np.std(pm25_values):.2f}\n")
            else:
                print("⚠️  No readings found for this node\n")
            
            # Get AQI history
            aqi_history = self.db.get_aqi_24h_history(node_id)
            
            if aqi_history:
                print(f"AQI History (last 24h): {len(aqi_history)} records\n")
                
                latest_aqi = aqi_history[-1]
                print("Latest AQI:")
                print(f"  Timestamp: {latest_aqi.timestamp}")
                print(f"  AQI Value: {latest_aqi.aqi_value:.1f}")
                print(f"  Category: {latest_aqi.aqi_category}")
                print(f"  Dominant Pollutant: {latest_aqi.dominant_pollutant}\n")
                
                aqi_values = [a.aqi_value for a in aqi_history]
                print("AQI Statistics (24h):")
                print(f"  Average: {np.mean(aqi_values):.1f}")
                print(f"  Max: {np.max(aqi_values):.1f}")
                print(f"  Min: {np.min(aqi_values):.1f}\n")
        except Exception as e:
            logger.error(f"Error: {e}")
    
    def run_full_cycle(self):
        """Run complete monitoring cycle"""
        print("\n" + "="*70)
        print("RUNNING COMPLETE MONITORING CYCLE")
        print("="*70)
        
        try:
            # Step 1: Collect data
            if not self.collect_24h_data():
                return False
            
            # Step 2: Calculate AQI
            self.calculate_aqi_for_all()
            
            # Step 3: Generate heatmap
            self.generate_heatmap()
            
            # Step 4: Display summary
            self.display_summary()
            
            print("="*70)
            print("✅ COMPLETE MONITORING CYCLE FINISHED SUCCESSFULLY!")
            print("="*70 + "\n")
            
            return True
        except Exception as e:
            logger.error(f"Error in full cycle: {e}")
            return False
    
    def close(self):
        """Close all connections"""
        try:
            self.collector.close()
            self.db.close()
            logger.info("✓ All connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")


# Main execution
def main():
    """Main function"""
    system = None
    
    try:
        # Initialize system
        system = AirQualityMonitoringSystem()
        
        # Run full monitoring cycle
        system.run_full_cycle()
        
        # Display specific node details
        print("\n" + "-"*70)
        system.display_node_details('node_1')
        
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. View heatmap: Open 'static/heatmap.html' in web browser")
        print("2. Dashboard: Run 'python flask_app.py' for web interface")
        print("3. Scheduled monitoring: Set up APScheduler for real-time updates")
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  System interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if system:
            system.close()


if __name__ == "__main__":
    main()