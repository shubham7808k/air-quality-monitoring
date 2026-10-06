from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import logging
import os
from config import DATABASE_URL, DATA_RETENTION_HOURS, TIMEZONE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(DATABASE_URL, echo=False, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============= DATABASE MODELS =============

class SensorReading(Base):
    """Store raw sensor measurements - Last 24 hours window"""
    __tablename__ = 'sensor_readings'
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Raw measurements
    pm25 = Column(Float, nullable=False)
    pm10 = Column(Float, nullable=False)
    no2 = Column(Float, nullable=True, default=0.0)
    co = Column(Float, nullable=True, default=0.0)
    
    # Environmental parameters
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    
    # Calibration info
    is_calibrated = Column(Boolean, default=False)
    calibrated_pm25 = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<SensorReading({self.node_id}, {self.timestamp}, PM25={self.pm25})>"


class AQIValue(Base):
    """Store calculated AQI values"""
    __tablename__ = 'aqi_values'
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    aqi_value = Column(Float, nullable=False)
    aqi_category = Column(String(50), nullable=False)
    dominant_pollutant = Column(String(50), nullable=True)
    color_code = Column(String(7), nullable=True)
    
    def __repr__(self):
        return f"<AQIValue({self.node_id}, {self.aqi_value}, {self.aqi_category})>"


class AQIPrediction(Base):
    """Store AQI predictions"""
    __tablename__ = 'aqi_predictions'
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), nullable=False, index=True)
    prediction_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    hours_ahead = Column(Integer, nullable=False)
    predicted_aqi = Column(Float, nullable=False)
    predicted_category = Column(String(50), nullable=False)
    confidence_score = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<AQIPrediction({self.node_id}, +{self.hours_ahead}h, AQI={self.predicted_aqi})>"


# Create tables
Base.metadata.create_all(bind=engine)
logger.info("✓ Database tables created")


# ============= DATABASE MANAGER =============

class DatabaseManager:
    """Manage all database operations"""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def add_sensor_reading(self, reading_dict):
        """Insert sensor reading"""
        try:
            reading = SensorReading(**reading_dict)
            self.session.add(reading)
            self._cleanup_old_data()
            self.session.commit()
            return reading
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding reading: {e}")
            return None
    
    def get_last_24h_readings(self, node_id):
        """Get last 24 hours of readings"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            readings = self.session.query(SensorReading).filter(
                SensorReading.node_id == node_id,
                SensorReading.timestamp >= cutoff_time
            ).order_by(SensorReading.timestamp.asc()).all()
            return readings
        except Exception as e:
            logger.error(f"Error fetching readings: {e}")
            return []
    
    def get_latest_reading_all_nodes(self):
        """Get most recent reading from each node"""
        try:
            subquery = self.session.query(
                SensorReading.node_id,
                func.max(SensorReading.timestamp).label('max_time')
            ).filter(
                SensorReading.timestamp >= datetime.now(timezone.utc) - timedelta(hours=24)
            ).group_by(SensorReading.node_id).subquery()
            
            latest = self.session.query(SensorReading).join(
                subquery,
                (SensorReading.node_id == subquery.c.node_id) &
                (SensorReading.timestamp == subquery.c.max_time)
            ).all()
            
            return latest
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    
    def add_aqi_value(self, aqi_dict):
        """Insert AQI value"""
        try:
            aqi = AQIValue(**aqi_dict)
            self.session.add(aqi)
            self.session.commit()
            return aqi
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding AQI: {e}")
            return None
    
    def get_latest_aqi_all_nodes(self):
        """Get latest AQI for all nodes"""
        try:
            subquery = self.session.query(
                AQIValue.node_id,
                func.max(AQIValue.timestamp).label('max_time')
            ).filter(
                AQIValue.timestamp >= datetime.now(timezone.utc) - timedelta(hours=24)
            ).group_by(AQIValue.node_id).subquery()
            
            latest = self.session.query(AQIValue).join(
                subquery,
                (AQIValue.node_id == subquery.c.node_id) &
                (AQIValue.timestamp == subquery.c.max_time)
            ).all()
            
            return latest
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    
    def get_aqi_24h_history(self, node_id):
        """Get AQI history for last 24 hours"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            aqi_values = self.session.query(AQIValue).filter(
                AQIValue.node_id == node_id,
                AQIValue.timestamp >= cutoff_time
            ).order_by(AQIValue.timestamp.asc()).all()
            return aqi_values
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    
    def add_prediction(self, prediction_dict):
        """Insert prediction"""
        try:
            prediction = AQIPrediction(**prediction_dict)
            self.session.add(prediction)
            self.session.commit()
            return prediction
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding prediction: {e}")
            return None
    
    def _cleanup_old_data(self):
        """Delete data older than 24 hours"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=DATA_RETENTION_HOURS)
            
            self.session.query(SensorReading).filter(
                SensorReading.timestamp < cutoff_time
            ).delete()
            
            self.session.query(AQIValue).filter(
                AQIValue.timestamp < cutoff_time
            ).delete()
            
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Cleanup error: {e}")
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            stats = {
                'total_readings': self.session.query(SensorReading).count(),
                'readings_24h': self.session.query(SensorReading).filter(
                    SensorReading.timestamp >= datetime.now(timezone.utc) - timedelta(hours=24)
                ).count(),
                'total_aqi': self.session.query(AQIValue).count(),
                'active_nodes': self.session.query(SensorReading.node_id).distinct().count()
            }
            return stats
        except Exception as e:
            logger.error(f"Error: {e}")
            return {}
    
    def close(self):
        """Close database session"""
        self.session.close()


# Test
if __name__ == "__main__":
    db = DatabaseManager()
    stats = db.get_database_stats()
    print("Database Stats:", stats)
    db.close()