
"""
arduino_aqi.py

GP2Y1010AU0F: uncalibrated dust concentration estimate.
MQ-135: raw gas sensor reading, not PM10.
Not an official CPCB AQI calculation.
"""


def process_sensor_data(sensor_data):
    try:
        dust_adc = float(sensor_data["dust_adc"])
        mq135_adc = float(sensor_data["mq135_adc"])

        if not 0 <= dust_adc <= 1023:
            raise ValueError("Invalid dust ADC reading")

        if not 0 <= mq135_adc <= 1023:
            raise ValueError("Invalid MQ-135 ADC reading")

        # GP2Y1010AU0F dust sensor conversion.
        # Assumes 5 V analog reference.
        dust_voltage = dust_adc * 5.0 / 1023.0

        # Typical approximate sensor baseline and sensitivity.
        dust_mg_m3 = max(
            0.0,
            (dust_voltage - 0.9) / 5.0
        )

        pm25_estimate = dust_mg_m3 * 1000.0

        # MQ-135 is a gas sensor; do not label this as PM10.
        gas_adc = round(mq135_adc, 1)

        # Experimental combined index; NOT official AQI.
        dust_index = dust_adc / 1023.0 * 100
        gas_index = mq135_adc / 1023.0 * 100
        experimental_index = round((dust_index + gas_index) / 2)

        if experimental_index <= 20:
            status = "Low sensor index"
        elif experimental_index <= 40:
            status = "Moderate sensor index"
        elif experimental_index <= 60:
            status = "Elevated sensor index"
        elif experimental_index <= 80:
            status = "High sensor index"
        else:
            status = "Very high sensor index"

        return {
            "aqi": experimental_index,
            "status": status,
            "dust_adc": round(dust_adc, 1),
            "dust_voltage": round(dust_voltage, 3),
            "pm25_estimate_ug_m3": round(pm25_estimate, 1),
            "mq135_adc": gas_adc,
            "gas_sensor_value": gas_adc,
            "temperature_c": sensor_data.get("temperature_c"),
            "humidity": sensor_data.get("humidity"),
            "calculation": (
                "Experimental index, not official CPCB AQI. "
                "PM2.5 is an uncalibrated dust estimate. "
                "MQ-135 does not measure PM10."
            )
        }

    except (KeyError, TypeError, ValueError) as error:
        return {
            "aqi": None,
            "status": "Invalid sensor data",
            "error": str(error)
        }


if __name__ == "__main__":
    sample_data = {
        "dust_adc": 230,
        "mq135_adc": 99,
        "temperature_c": 26.7,
        "humidity": 63.9
    }

    print(process_sensor_data(sample_data))
