import random
import numpy as np
from datetime import datetime, timedelta, timezone
from backend.database_models import DatabaseManager
from config import SENSOR_NODES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SensorDataCollector:
    """Collect sensor data or generate simulated data"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def generate_simulated_reading(self, node_id, hour_offset=0):
        """Generate realistic simulated sensor data"""
        now = datetime.now(timezone.utc) - timedelta(hours=hour_offset)
        hour = now.hour
        
        # Pollution patterns by time of day
        if 7 <= hour <= 9:
            pm25_base = random.uniform(100, 150)
        elif 16 <= hour <= 18:
            pm25_base = random.uniform(90, 140)
        elif 10 <= hour <= 15:
            pm25_base = random.uniform(50, 80)
        elif 19 <= hour <= 23:
            pm25_base = random.uniform(40, 70)
        else:
            pm25_base = random.uniform(20, 50)
        
        pm25 = pm25_base + np.random.normal(0, 5)
        pm10 = pm25 * 1.5 + np.random.normal(0, 10)
        
        # NO2 and CO - higher during traffic
        if (7 <= hour <= 9) or (16 <= hour <= 18):
            no2 = random.uniform(50, 80)
            co = random.uniform(1.0, 3.0)
        else:
            no2 = random.uniform(20, 50)
            co = random.uniform(0.2, 1.0)
        
        # Temperature variation
        if 6 <= hour < 12:
            temp = 24 + (hour - 6) * 1.5 + random.uniform(-2, 2)
        elif 12 <= hour < 18:
            temp = 30 + random.uniform(-3, 5)
        else:
            temp = 20 + random.uniform(-3, 3)
        
        # Humidity
        if 6 <= hour < 12:
            humidity = 70 - (hour - 6) * 3 + random.uniform(-5, 5)
        elif 12 <= hour < 18:
            humidity = 45 + random.uniform(-5, 10)
        else:
            humidity = 75 + random.uniform(-10, 5)
        
        humidity = np.clip(humidity, 20, 95)
        
        return {
            'node_id': node_id,
            'timestamp': now,
            'pm25': np.clip(pm25, 0, 1000),
            'pm10': np.clip(pm10, 0, 1500),
            'no2': np.clip(no2, 0, 500),
            'co': np.clip(co, 0, 100),
            'temperature': np.clip(temp, -40, 60),
            'humidity': np.clip(humidity, 0, 100),
            'is_calibrated': False
        }
    
    def collect_all_sensors(self, use_simulation=True):
        """Collect from all sensor nodes"""
        all_readings = []
        
        for node_id in SENSOR_NODES.keys():
            try:
                reading = self.generate_simulated_reading(node_id)
                self.db.add_sensor_reading(reading)
                all_readings.append(reading)
                logger.info(f"✓ {node_id}: PM2.5={reading['pm25']:.1f}")
            except Exception as e:
                logger.error(f"✗ {node_id}: {e}")
        
        return all_readings
    
    def collect_multiple_intervals(self, num_intervals=24):
        """Collect data for multiple time intervals"""
        logger.info(f"Collecting {num_intervals} intervals of data...")
        
        for hour_offset in range(num_intervals):
            logger.info(f"Hour -{hour_offset}h")
            for node_id in SENSOR_NODES.keys():
                reading = self.generate_simulated_reading(node_id, hour_offset=hour_offset)
                self.db.add_sensor_reading(reading)
        
        logger.info(f"✓ Collected data for {num_intervals} hours")
    
    def close(self):
        """Close database"""
        self.db.close()


if __name__ == "__main__":
    collector = SensorDataCollector()
    collector.collect_multiple_intervals(24)
    stats = collector.db.get_database_stats()
    print("Database Stats:", stats)
    collector.close()