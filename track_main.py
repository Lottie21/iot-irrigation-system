# main.py
from usage_tracker import UsageTracker
import RPi.GPIO as GPIO
import time

tracker = UsageTracker()

PUMP_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_PIN, GPIO.OUT)

def pump_on(seconds):
    GPIO.output(PUMP_PIN, GPIO.HIGH)
    time.sleep(seconds)
    GPIO.output(PUMP_PIN, GPIO.LOW)

    # 这里填你实际测的水泵电压和电流
    voltage = 5.0
    current = 0.6

    entry = tracker.record_pump_run(seconds, voltage, current)
    print("Pump run recorded:", entry)


# Example run
pump_on(4)
print("Summary:", tracker.get_summary())