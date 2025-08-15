import argparse
import threading
import time
from gpiozero import MotionSensor
from src.motion_detector import MotionDetector
from src.motion_event_dao import MotionEventDao

class MotionSystem:
    def __init__(self, motion_sensor: MotionSensor, database: MotionEventDao, detector: MotionDetector):
        self.motion_sensor = motion_sensor
        self.database = database
        self.detector = detector

    def run(self, duration: int):
        print("Starting motion detection system...")
        print("Waiting for sensor to settle...")
        try:
            # Let the motion detector handle sensor stabilization
            self.detector.wait_for_sensor_ready()

            if duration > 0:
                # Start monitoring in a separate thread so we can control timing
                monitor_thread = threading.Thread(target=self.detector.start_monitoring)
                monitor_thread.daemon = True
                monitor_thread.start()
                
                # Wait for the specified duration
                time.sleep(duration)
                
                # Stop monitoring
                print(f"\nMotion detection completed after {duration} seconds.")
                self.detector.stop_monitoring()
                
                # Give the thread a moment to finish
                time.sleep(0.5)
            else:
                # Run indefinitely until interrupted
                self.detector.start_monitoring()
        except KeyboardInterrupt:
            print("\nMotion detection system stopped by user.")
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
