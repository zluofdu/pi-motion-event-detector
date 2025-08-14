import datetime
from src.models.motion_event import MotionEvent

class MotionDetector:
    def __init__(self, sensor, database):
        self.sensor = sensor
        self.database = database
        # Generate device ID from the sensor's pin information
        pin_name = sensor.pin.name
        self.device_id = f"pir_sensor_{pin_name}"
        self._running = False

    def start_monitoring(self):
        """Start monitoring for motion events in a loop.
        The loop can be stopped by calling stop_monitoring()."""
        print("Starting motion detection...")
        self._running = True
        try:
            while self._running:
                self.capture_motion_event()
        except KeyboardInterrupt:
            self.stop_monitoring()
        except Exception as e:
            print(f"Error during motion detection: {e}")
            self.stop_monitoring()
            raise

    def stop_monitoring(self):
        """Stop the monitoring loop."""
        print("Stopping motion detection...")
        self._running = False

    def capture_motion_event(self):
        """Capture a single motion event."""
        self.sensor.wait_for_motion()
        if not self._running:  # Check if we should stop
            return
            
        start_timestamp = datetime.datetime.now()
        print(f"Motion detected at {start_timestamp}")
        
        self.sensor.wait_for_no_motion()
        if not self._running:  # Check if we should stop
            return
            
        stop_timestamp = datetime.datetime.now()
        print(f"Motion stopped at {stop_timestamp}")
        
        event = MotionEvent(
            device_id=self.device_id,
            start_timestamp=start_timestamp,
            stop_timestamp=stop_timestamp
        )
        self.database.add(event)