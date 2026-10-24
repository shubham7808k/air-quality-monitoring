import os
from datetime import timedelta
import pytz

# ============= BASIC CONFIGURATION =============
APP_NAME = "Hyperlocal Air Quality Monitoring System"
DEBUG_MODE = True
TIMEZONE = pytz.timezone('Asia/Kolkata')

# ============= DATA RETENTION =============
DATA_RETENTION_HOURS = 24
REFRESH_INTERVAL_MINUTES = 15

# ============= SENSOR NODE CONFIGURATION =============
SENSOR_NODES = {
    'node_1': {
        'name': 'School Gate',
        'latitude': 26.8467,
        'longitude': 80.9462,
        'location_type': 'high_traffic',
        'description': 'Main entrance with heavy vehicle traffic'
    },
    'node_2': {
        'name': 'Playground',
        'latitude': 26.8468,
        'longitude': 80.9463,
        'location_type': 'outdoor_activity',
        'description': 'Student outdoor activity area'
    },
    'node_3': {
        'name': 'Campus Center',
        'latitude': 26.8469,
        'longitude': 80.9464,
        'location_type': 'general',
        'description': 'Central campus location'
    },
    'node_4': {
        'name': 'Roadside',
        'latitude': 26.8470,
        'longitude': 80.9465,
        'location_type': 'high_traffic',
        'description': 'Adjacent road with regular traffic'
    },
    'node_5': {
        'name': 'Classroom Block',
        'latitude': 26.8467,
        'longitude': 80.9462,
        'location_type': 'indoor',
        'description': 'Indoor air quality monitoring'
    }
}

# ============= AQI CATEGORIES =============
AQI_CATEGORIES = {
    'Good': (0, 50, '#00C853'),
    'Satisfactory': (51, 100, '#FBC02D'),
    'Moderately Polluted': (101, 200, '#F57C00'),
    'Poor': (201, 300, '#D32F2F'),
    'Very Poor': (301, 400, '#7B1FA2'),
    'Severe': (401, 500, '#4A148C')
}

# ============= POLLUTANT BREAKPOINTS =============
POLLUTANT_BREAKPOINTS = {
    'PM25': {
        'ranges': [
            (0, 30, 0, 50),
            (31, 60, 51, 100),
            (61, 90, 101, 200),
            (91, 120, 201, 300),
            (121, 250, 301, 400),
            (251, 1000, 401, 500)
        ]
    },
    'PM10': {
        'ranges': [
            (0, 50, 0, 50),
            (51, 100, 51, 100),
            (101, 250, 101, 200),
            (251, 350, 201, 300),
            (351, 430, 301, 400),
            (431, 1000, 401, 500)
        ]
    },
    'NO2': {
        'ranges': [
            (0, 40, 0, 50),
            (41, 80, 51, 100),
            (81, 180, 101, 200),
            (181, 280, 201, 300),
            (281, 400, 301, 400),
            (401, 1000, 401, 500)
        ]
    },
    'CO': {
        'ranges': [
            (0, 1, 0, 50),
            (1.1, 2, 51, 100),
            (2.1, 10, 101, 200),
            (10.1, 17, 201, 300),
            (17.1, 34, 301, 400),
            (34.1, 100, 401, 500)
        ]
    }
}

# ============= DATABASE CONFIGURATION =============
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = 'sqlite:///' + os.path.join(BASE_DIR, 'data', 'air_quality.db')

# ============= SCHOOL HOURS =============
SCHOOL_HOURS = {
    'start': 9,
    'end': 16,
    'lunch_start': 12,
    'lunch_end': 13,
    'break_start': 15,
    'break_end': 15.5
}

# ============= PREDICTION PARAMETERS =============
PREDICTION_HORIZONS = [6, 12, 24]
LOOKBACK_PERIOD_HOURS = 168

# ============= DATA VALIDATION =============
DATA_VALIDATION = {
    'PM25': {'min': 0, 'max': 1000},
    'PM10': {'min': 0, 'max': 1500},
    'NO2': {'min': 0, 'max': 500},
    'CO': {'min': 0, 'max': 100},
    'TEMPERATURE': {'min': -40, 'max': 60},
    'HUMIDITY': {'min': 0, 'max': 100}
}

# ============= API CONFIGURATION =============
API_HOST = '0.0.0.0'
API_PORT = 5000

# ============= LOGGING =============
LOG_LEVEL = 'INFO'
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'system.log')

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

ARDUINO_SERIAL_PORT = "COM13"
ARDUINO_BAUD_RATE = 9600