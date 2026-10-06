import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAQIPredictor:
    """Simple AQI prediction using moving average and trend"""
    
    def __init__(self, sequence_length=24):
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler()
    
    def predict_aqi(self, aqi_history, hours_ahead=24):
        """Predict AQI for next N hours using trend"""
        if len(aqi_history) < self.sequence_length:
            logger.warning("Insufficient historical data")
            return np.full(hours_ahead, np.mean(aqi_history))
        
        # Calculate trend
        recent = np.array(aqi_history[-self.sequence_length:])
        
        # Linear regression for trend
        x = np.arange(len(recent))
        z = np.polyfit(x, recent, 1)
        trend = z[0]  # slope
        
        # Make predictions
        last_value = aqi_history[-1]
        predictions = []
        
        for i in range(1, hours_ahead + 1):
            # Combine trend with mean reversion
            predicted = last_value + (trend * i) + np.random.normal(0, 2)
            predicted = np.clip(predicted, 0, 500)
            predictions.append(predicted)
        
        return np.array(predictions)
    
    def get_24h_forecast(self, aqi_history):
        """Get 24-hour forecast"""
        return self.predict_aqi(aqi_history, hours_ahead=24)


if __name__ == "__main__":
    predictor = SimpleAQIPredictor()
    
    # Test data
    history = np.random.uniform(60, 120, 168)  # 7 days
    forecast = predictor.get_24h_forecast(history)
    
    print("AQI History (last 24h):", history[-24:])
    print("24h Forecast:", forecast)