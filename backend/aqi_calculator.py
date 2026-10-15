
"""CPCB-style particulate sub-index calculator.

This calculates experimental PM2.5 and PM10 sub-indices.
It does NOT determine official overall AQI by itself.
Concentrations must be validated measurements in µg/m³.
"""

PM25_BREAKPOINTS = [
    (0, 30, 0, 50),
    (30, 60, 50, 100),
    (60, 90, 100, 200),
    (90, 120, 200, 300),
    (120, 250, 300, 400),
    (250, float("inf"), 400, 500),
]

PM10_BREAKPOINTS = [
    (0, 50, 0, 50),
    (50, 100, 50, 100),
    (100, 250, 100, 200),
    (250, 350, 200, 300),
    (350, 430, 300, 400),
    (430, float("inf"), 400, 500),
]


def calculate_sub_index(concentration, breakpoints):
    """Return a pollutant sub-index from concentration in µg/m³."""
    if concentration is None:
        return None

    try:
        concentration = float(concentration)
    except (TypeError, ValueError):
        return None

    if concentration < 0:
        return None

    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= concentration <= c_high:
            if c_high == float("inf"):
                return 500

            # Linear interpolation between breakpoint values
            index = (
                (i_high - i_low)
                / (c_high - c_low)
                * (concentration - c_low)
                + i_low
            )
            return round(index)

    return None


def calculate_particle_sub_indices(pm25=None, pm10=None):
    """Calculate experimental particle sub-indices, not overall AQI."""
    return {
        "pm25_sub_index": calculate_sub_index(
            pm25, PM25_BREAKPOINTS
        ),
        "pm10_sub_index": calculate_sub_index(
            pm10, PM10_BREAKPOINTS
        ),
        "overall_aqi": None,
        "status": "Insufficient data for official overall AQI",
    }
