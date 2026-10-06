import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib
import os
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SensorCalibration:
    """Calibrate sensor data using ML models"""
    
    def __init__(self):
        self.rf_model = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
        self.gb_model = GradientBoostingRegressor(n_estimators=150, learning_rate=0.05, max_depth=5)
        self.scaler = StandardScaler()
        
    def prepare_training_data(self, sensor_df, reference_df):
        """Prepare training data - last 24 hours"""
        current_time = pd.Timestamp.now(tz='UTC')
        cutoff_time = current_time - timedelta(hours=24)
        
        sensor_df['timestamp'] = pd.to_datetime(sensor_df['timestamp'], utc=True)
        reference_df['timestamp'] = pd.to_datetime(reference_df['timestamp'], utc=True)
        
        sensor_24h = sensor_df[sensor_df['timestamp'] >= cutoff_time].copy()
        reference_24h = reference_df[reference_df['timestamp'] >= cutoff_time].copy()
        
        sensor_24h.set_index('timestamp', inplace=True)
        reference_24h.set_index('timestamp', inplace=True)
        
        merged = pd.merge_asof(
            sensor_24h.sort_index(),
            reference_24h.sort_index(),
            left_index=True,
            right_index=True,
            direction='nearest',
            tolerance=pd.Timedelta('5 min'),
            suffixes=('_sensor', '_reference')
        )
        
        return merged.reset_index()
    
    def train_calibration_model(self, sensor_df, reference_df, pollutant='PM25'):
        """Train calibration model"""
        merged_data = self.prepare_training_data(sensor_df, reference_df)
        
        if len(merged_data) < 10:
            logger.warning("Insufficient training data")
            return None
        
        features = ['PM25_sensor', 'PM10_sensor', 'temperature', 'humidity', 'CO_sensor']
        X = merged_data[features].copy()
        y = merged_data[f'{pollutant}_reference'].copy()
        
        valid_idx = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_idx]
        y = y[valid_idx]
        
        if len(X) < 10:
            logger.warning("Insufficient data after cleaning")
            return None
        
        X_scaled = self.scaler.fit_transform(X)
        
        self.rf_model.fit(X_scaled, y)
        self.gb_model.fit(X_scaled, y)
        
        rf_pred = self.rf_model.predict(X_scaled)
        gb_pred = self.gb_model.predict(X_scaled)
        
        rf_r2 = r2_score(y, rf_pred)
        rf_rmse = np.sqrt(mean_squared_error(y, rf_pred))
        gb_r2 = r2_score(y, gb_pred)
        gb_rmse = np.sqrt(mean_squared_error(y, gb_pred))
        
        logger.info(f"\nCalibration Results:")
        logger.info(f"Random Forest - R²: {rf_r2:.4f}, RMSE: {rf_rmse:.2f}")
        logger.info(f"Gradient Boosting - R²: {gb_r2:.4f}, RMSE: {gb_rmse:.2f}")
        
        return {
            'rf_r2': rf_r2, 'rf_rmse': rf_rmse,
            'gb_r2': gb_r2, 'gb_rmse': gb_rmse,
            'samples': len(X)
        }
    
    def calibrate_sensor_data(self, sensor_reading, use_model='rf'):
        """Apply calibration to sensor reading"""
        features = ['PM25', 'PM10', 'temperature', 'humidity', 'CO']
        sensor_array = np.array([[sensor_reading.get(f, 0) for f in features]])
        sensor_scaled = self.scaler.transform(sensor_array)
        
        if use_model == 'rf':
            calibrated = self.rf_model.predict(sensor_scaled)[0]
        else:
            calibrated = self.gb_model.predict(sensor_scaled)[0]
        
        return max(0, calibrated)
    
    def save_models(self, path='data/models/'):
        """Save trained models"""
        os.makedirs(path, exist_ok=True)
        joblib.dump(self.rf_model, f'{path}rf_calibration.pkl')
        joblib.dump(self.gb_model, f'{path}gb_calibration.pkl')
        joblib.dump(self.scaler, f'{path}scaler.pkl')
        logger.info(f"✓ Models saved to {path}")
    
    def load_models(self, path='data/models/'):
        """Load pre-trained models"""
        try:
            self.rf_model = joblib.load(f'{path}rf_calibration.pkl')
            self.gb_model = joblib.load(f'{path}gb_calibration.pkl')
            self.scaler = joblib.load(f'{path}scaler.pkl')
            logger.info(f"✓ Models loaded from {path}")
        except:
            logger.warning("Could not load models")


if __name__ == "__main__":
    # Test calibration
    calib = SensorCalibration()
    
    n_samples = 96
    timestamps = pd.date_range(end=datetime.now(tz=timezone.utc), periods=n_samples, freq='15min')
    
    sensor_df = pd.DataFrame({
        'timestamp': timestamps,
        'PM25_sensor': np.random.uniform(40, 100, n_samples),
        'PM10_sensor': np.random.uniform(60, 150, n_samples),
        'temperature': np.random.uniform(25, 35, n_samples),
        'humidity': np.random.uniform(50, 80, n_samples),
        'CO_sensor': np.random.uniform(0.5, 2, n_samples)
    })
    
    reference_df = pd.DataFrame({
        'timestamp': timestamps,
        'PM25': np.random.uniform(35, 95, n_samples)
    })
    
    result = calib.train_calibration_model(sensor_df, reference_df)
    print("Calibration complete:", result)