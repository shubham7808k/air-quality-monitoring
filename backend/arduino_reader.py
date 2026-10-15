
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

    def parse_line(self, line):
        parts = line.strip().split(",")

        # Arduino sends: dustRaw,dustVoltage,mqRaw
        if len(parts) != 3:
            return None

        try:
            dust_raw = int(parts[0])
            dust_voltage = float(parts[1])
            mq_raw = int(parts[2])
        except (ValueError, TypeError):
            return None

        return {
            "timestamp": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "dust_raw": dust_raw,
            "dust_voltage": dust_voltage,
            "mq_raw": mq_raw,
            "source": "arduino"
        }

    def start(self):
        with self.lock:
            if self.running:
                return

            self.running = True
            self.thread = threading.Thread(
                target=self._read_loop,
                daemon=True
            )
            self.thread.start()

    def _read_loop(self):
        while self.running:
            try:
                with serial.Serial(
                    ARDUINO_SERIAL_PORT,
                    ARDUINO_BAUD_RATE,
                    timeout=1
                ) as connection:
                    with self.lock:
                        self.error = None

                    while self.running:
                        line = connection.readline().decode(
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

            except (SerialException, OSError) as exc:
                with self.lock:
                    self.error = (
                        f"Cannot read {ARDUINO_SERIAL_PORT}: {exc}"
                    )
                time.sleep(3)

    def snapshot(self):
        with self.lock:
            latest = self.latest.copy() if self.latest else None
            history_count = len(self.history)
            error = self.error

        connected = latest is not None and error is None

        return {
            "connected": connected,
            "error": error,
            "latest": latest,
            "history_count": history_count
        }

    def get_history(self):
        with self.lock:
            return list(self.history)


arduino_reader = ArduinoSerialReader()