import datetime
import time
from src.models.motion_event import MotionEvent

class MotionDetector:
    def __init__(self, sensor, database):
        self.sensor = sensor
        self.database = database
        # Generate device ID from the sensor's pin information
        pin_name = str(sensor.pin)
        self.device_id = f"pir_sensor_{pin_name}"
        self._running = False

    def wait_for_sensor_ready(self):
        """Wait for the sensor to stabilize and be ready for monitoring."""
        print("Checking sensor status...")
        start_time = time.time()
        stable_count = 0
        required_stable_readings = 5  # Need 5 consecutive stable readings
        
        while stable_count < required_stable_readings:
            current_state = self.sensor.value
            time.sleep(0.1)  # Small delay between readings
            next_state = self.sensor.value
            
            if current_state == next_state:
                stable_count += 1
                print(f"Sensor stable: {stable_count}/{required_stable_readings}")
            else:
                stable_count = 0  # Reset if state changes
                print("Sensor state changed, waiting for stability...")
            
            # Safety timeout to prevent infinite loop
            if time.time() - start_time > 10:
                print("Sensor stabilization timeout reached, proceeding anyway...")
                break
        
        print("Sensor is ready!")

    def start_monitoring(self):
        """Start monitoring for motion events in a loop.
        The loop can be stopped by calling stop_monitoring()."""
        print("Starting motion detection...")
        self._running = True
        try:
            while self._running:
                self.capture_motion_event()
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