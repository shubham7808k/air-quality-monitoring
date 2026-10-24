
import json
import math
import threading
import time
from collections import deque
from datetime import datetime

import serial
from serial import SerialException

from config import ARDUINO_SERIAL_PORT, ARDUINO_BAUD_RATE


class ArduinoSerialReader:
    def __init__(self):
        self.lock = threading.Lock()
        self.latest = None
        self.history = deque(maxlen=500)
        self.error = "Waiting for Arduino connection"
        self.running = False
        self.thread = None

    @staticmethod
    def to_float(value):
        """Convert a sensor value to a finite float."""
        number = float(value)

        if not math.isfinite(number):
            raise ValueError("Sensor value must be finite")

        return number

    def parse_line(self, line):
        """Parse one JSON reading received from Arduino."""
        try:
            data = json.loads(line.strip())

            required = (
                "dust_adc",
                "mq135_adc",
                "temperature_c",
                "humidity",
            )

            if not isinstance(data, dict):
                return None

            if not all(key in data for key in required):
                return None

            reading = {
                "timestamp": datetime.now().astimezone().isoformat(
                    timespec="seconds"
                ),
                "dust_adc": self.to_float(data["dust_adc"]),
                "mq135_adc": self.to_float(data["mq135_adc"]),
                "temperature_c": self.to_float(data["temperature_c"]),
                "humidity": self.to_float(data["humidity"]),
                "source": "arduino",
            }

            return reading

        except (json.JSONDecodeError, TypeError, ValueError):
            return None

    def start(self):
        """Start the background serial-reading thread."""
        with self.lock:
            if self.running:
                return

            self.running = True
            self.thread = threading.Thread(
                target=self._read_loop,
                daemon=True,
                name="ArduinoSerialReader",
            )
            self.thread.start()

    def _read_loop(self):
        """Continuously read sensor data from the Arduino USB port."""
        while self.running:
            try:
                with serial.Serial(
                    ARDUINO_SERIAL_PORT,
                    ARDUINO_BAUD_RATE,
                    timeout=1,
                ) as connection:

                    # Allow the Arduino to reset after serial connection.
                    time.sleep(2)
                    connection.reset_input_buffer()

                    while self.running:
                        raw_line = connection.readline()

                        if not raw_line:
                            continue

                        line = raw_line.decode(
                            "utf-8", errors="ignore"
                        ).strip()

                        if not line:
                            continue

                        reading = self.parse_line(line)

                        if reading is None:
                            continue

                        with self.lock:
                            self.latest = reading
                            self.history.append(reading)
                            self.error = None

            except (SerialException, OSError) as exc:
                with self.lock:
                    self.error = (
                        f"Cannot read {ARDUINO_SERIAL_PORT}: {exc}"
                    )

                time.sleep(3)

    def snapshot(self):
        """Return the latest reading and connection status."""
        with self.lock:
            latest = self.latest.copy() if self.latest else None
            history_count = len(self.history)
            error = self.error

        connected = latest is not None and error is None

        return {
            "connected": connected,
            "error": error,
            "latest": latest,
            "history_count": history_count,
        }

    def get_history(self):
        """Return stored sensor readings."""
        with self.lock:
            return list(self.history)


arduino_reader = ArduinoSerialReader()
