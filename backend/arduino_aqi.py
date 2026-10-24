
def calculate_sub_index(concentration, breakpoints):
    """Calculate an AQI sub-index from a calibrated concentration."""
    if concentration is None or concentration < 0:
        return None

    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= concentration <= c_high:
            return round(
                ((i_high - i_low) / (c_high - c_low))
                * (concentration - c_low)
                + i_low
            )

    return None


PM25_BREAKPOINTS = [
    (0, 30, 0, 50),
    (30, 60, 50, 100),
    (60, 90, 100, 200),
    (90, 120, 200, 300),
    (120, 250, 300, 400),
    (250, 500, 400, 500),
]

PM10_BREAKPOINTS = [
    (0, 50, 0, 50),
    (50, 100, 50, 100),
    (100, 250, 100, 200),
    (250, 350, 200, 300),
    (350, 430, 300, 400),
    (430, 600, 400, 500),
]


def calculate_particle_aqi(pm25=None, pm10=None):
    pm25_index = calculate_sub_index(pm25, PM25_BREAKPOINTS)
    pm10_index = calculate_sub_index(pm10, PM10_BREAKPOINTS)

    available = [
        value for value in (pm25_index, pm10_index)
        if value is not None
    ]

    return {
        "particle_index": max(available) if available else None,
        "pm25_index": pm25_index,
        "pm10_index": pm10_index,
        "is_official_aqi": False,
        "status": (
            "Experimental particle index"
            if available else "Calibration required"
        ),
    }


def process_sensor_data(sensor_data):
    """Return one experimental index from live sensor ADC readings."""

    if not isinstance(sensor_data, dict):
        sensor_data = {}

    try:
        dust = int(sensor_data["dust_adc"])
        gas = int(sensor_data["mq135_adc"])

        if not (0 <= dust <= 1023 and 0 <= gas <= 1023):
            raise ValueError("ADC values out of range")

    except (KeyError, TypeError, ValueError):
        return {
            "aqi": None,
            "status": "Waiting for valid sensor readings",
            "is_official_aqi": False
        }

    # Experimental normalized response, NOT official AQI.
    dust_percent = dust / 1023 * 100
    gas_percent = gas / 1023 * 100

    single_value = round((dust_percent + gas_percent) / 2)

    return {
        "aqi": single_value,
        "status": "Experimental sensor index — not official AQI",
        "is_official_aqi": False
    }
