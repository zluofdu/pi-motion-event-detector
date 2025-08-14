import argparse
from gpiozero import MotionSensor
from src.motion_detector import MotionDetector
from src.motion_event_dao import MotionEventDao
import time

class MotionSystem:
    def __init__(self, motion_sensor: MotionSensor, database: MotionEventDao, detector: MotionDetector):
        self.motion_sensor = motion_sensor
        self.database = database
        self.detector = detector

    def run(self, duration: int):
        print("Starting motion detection system...")
        print("Waiting for sensor to settle...")
        try:
            time.sleep(2)  # Wait for the sensor to stabilize

            if duration > 0:
                # Start monitoring and set up duration timer
                self.detector.start_monitoring()
                try:
                    time.sleep(duration)
                finally:
                    # Always ensure we stop monitoring even if interrupted
                    self.detector.stop_monitoring()
            else:
                # Run indefinitely until interrupted
                self.detector.start_monitoring()
        except KeyboardInterrupt:
            print("\nMotion detection system stopped by user.")
            # Only call stop_monitoring if we haven't already
            if duration <= 0:
                self.detector.stop_monitoring()

def create_system():
    motion_sensor = MotionSensor(4)
    database = MotionEventDao()
    detector = MotionDetector(motion_sensor, database)
    return MotionSystem(motion_sensor, database, detector)

def main():
    parser = argparse.ArgumentParser(description='Motion detection system')
    parser.add_argument('duration', type=int, help='Duration to run in seconds')
    args = parser.parse_args()

    system = create_system()
    system.run(args.duration)

if __name__ == "__main__":
    main()