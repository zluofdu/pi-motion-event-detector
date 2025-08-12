import datetime
from src.models.motion_event import MotionEvent

class MotionDetector:
    def __init__(self, sensor, database):
        self.sensor = sensor
        self.database = database

    def start_monitoring(self):
        print("Starting motion detection...")
        for _ in range(2):  # Run 2 times for testing
            self.capture_motion_event()

    def capture_motion_event(self):
        self.sensor.wait_for_motion()
        start_timestamp = datetime.datetime.now()
        if self.is_night_time(start_timestamp):
            print(f"Motion detected at {start_timestamp}")
            self.sensor.wait_for_no_motion()
            stop_timestamp = datetime.datetime.now()
            print(f"Motion stopped at {stop_timestamp}")
            event = MotionEvent(
                description=f"Motion detected at {start_timestamp}, stopped at {stop_timestamp}",
                start_timestamp=start_timestamp,
                stop_timestamp=stop_timestamp
            )
            self.database.add(event)
        else:
            self.sensor.wait_for_no_motion()
            print("Motion stopped (not night time)")

    def is_night_time(self, timestamp):
        return timestamp.hour < 6 or timestamp.hour >= 18  # Example: night time is from 6 PM to 6 AM