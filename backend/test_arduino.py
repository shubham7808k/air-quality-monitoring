
import serial
import time

PORT = "COM11"
BAUD_RATE = 9600

try:
    with serial.Serial(PORT, BAUD_RATE, timeout=2) as arduino:
        print(f"Connected to Arduino on {PORT}")
        time.sleep(2)  # Allow the Arduino to reset

        for _ in range(10):
            line = arduino.readline().decode(
                "utf-8", errors="replace"
            ).strip()

            if line:
                print("Arduino:", line)

except serial.SerialException as e:
    print("Serial connection failed:", e)
