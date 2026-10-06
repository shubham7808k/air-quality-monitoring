import numpy as np
from datetime import datetime, timezone
from config import AQI_CATEGORIES, POLLUTANT_BREAKPOINTS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AQICalculator:
    """Calculate Air Quality Index"""
    
    @staticmethod
    def get_subindex(pollutant_concentration, pollutant_type):
        """Calculate sub-index for specific pollutant"""
        if pollutant_type not in POLLUTANT_BREAKPOINTS:
            return 0
        
        ranges = POLLUTANT_BREAKPOINTS[pollutant_type]['ranges']
        
        for conc_low, conc_high, si_low, si_high in ranges:
            if conc_low <= pollutant_concentration <= conc_high:
                if conc_high == conc_low:
                    return si_low
                
                subindex = ((pollutant_concentration - conc_low) / (conc_high - conc_low)) * \
                          (si_high - si_low) + si_low
                return subindex
        
        if pollutant_concentration > ranges[-1][1]:
            return ranges[-1][3]
        
        return 0
    
    @staticmethod
    def calculate_aqi(sensor_reading):
        """Calculate overall AQI"""
        pm25 = sensor_reading.get('calibrated_pm25') or sensor_reading.get('pm25', 0)
        pm10 = sensor_reading.get('pm10', 0)
        no2 = sensor_reading.get('no2', 0)
        co = sensor_reading.get('co', 0)
        
        subindices = {
            'PM25': AQICalculator.get_subindex(pm25, 'PM25'),
            'PM10': AQICalculator.get_subindex(pm10, 'PM10'),
            'NO2': AQICalculator.get_subindex(no2, 'NO2'),
            'CO': AQICalculator.get_subindex(co, 'CO')
        }
        
        aqi_value = max(subindices.values()) if subindices else 0
        dominant_pollutant = max(subindices, key=subindices.get) if subindices else 'Unknown'
        
        category = 'Unknown'
        color = '#808080'
        
        for cat_name, (cat_low, cat_high, cat_color) in AQI_CATEGORIES.items():
            if cat_low <= aqi_value <= cat_high:
                category = cat_name
                color = cat_color
                break
        
        return {
            'value': round(aqi_value, 1),
            'category': category,
            'color': color,
            'dominant_pollutant': dominant_pollutant,
            'subindices': {k: round(v, 1) for k, v in subindices.items()},
            'timestamp': sensor_reading.get('timestamp', datetime.now(timezone.utc))
        }
    
    @staticmethod
    def get_health_advisory(aqi_category):
        """Get health recommendations"""
        advisories = {
            'Good': {
                'general': '✓ Air quality is Good. Enjoy outdoor activities!',
                'activities': 'All outdoor activities are safe.'
            },
            'Satisfactory': {
                'general': '◐ Air quality is Satisfactory.',
                'activities': 'Outdoor activities are generally fine.'
            },
            'Moderately Polluted': {
                'general': '◐ Moderate pollution. Sensitive groups should be cautious.',
                'activities': 'Limit outdoor exposure. Move sports indoors if possible.'
            },
            'Poor': {
                'general': '✗ Poor air quality. Minimize outdoor activities.',
                'activities': 'Avoid outdoor activities. Use air filters indoors.'
            },
            'Very Poor': {
                'general': '✗✗ Very poor air quality. Avoid outdoor exposure.',
                'activities': 'Cancel all outdoor activities. Use HEPA filters.'
            },
            'Severe': {
                'general': '✗✗✗ SEVERE air pollution. Health hazard.',
                'activities': 'ALL outdoor activities cancelled. Stay indoors.'
            }
        }
        
        return advisories.get(aqi_category, advisories['Good'])


if __name__ == "__main__":
    calc = AQICalculator()
    
    test_reading = {
        'pm25': 150,
        'pm10': 220,
        'no2': 80,
        'co': 2.0
    }
    
    result = calc.calculate_aqi(test_reading)
    print(f"AQI: {result['value']} - {result['category']}")
    print(f"Advisory: {calc.get_health_advisory(result['category'])['general']}")