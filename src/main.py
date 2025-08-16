import argparse
import threading
import time
from gpiozero import MotionSensor
from src.motion_detector import MotionDetector
from src.motion_event_dao import MotionEventDao
from src.timezone_utils import now_pst

class MotionSystem:
    def __init__(self, duration: int = 0):
        """Initialize the motion system with optional duration."""
        self.duration = duration
        
    def create_components(self):
        """Create the motion sensor, database, and detector components."""
        motion_sensor = MotionSensor(4)
        database = MotionEventDao()
        detector = MotionDetector(motion_sensor, database)
        return motion_sensor, database, detector

    def run(self):
        """Run the motion detection system."""
        motion_sensor, database, detector = self.create_components()
        
        print(f"Starting motion detection system at {now_pst().strftime('%Y-%m-%d %H:%M:%S %Z')}...")
        print("Waiting for sensor to settle...")
        try:
            # Let the motion detector handle sensor stabilization
            detector.wait_for_sensor_ready()

            if self.duration > 0:
                # Start monitoring in a separate thread so we can control timing
                monitor_thread = threading.Thread(target=detector.start_monitoring)
                monitor_thread.daemon = True
                monitor_thread.start()
                
                # Wait for the specified duration
                time.sleep(self.duration)
                
                # Stop monitoring
                print(f"\nMotion detection completed after {self.duration} seconds at {now_pst().strftime('%H:%M:%S %Z')}.")
                detector.stop_monitoring()
                
                # Give the thread a moment to finish
                time.sleep(0.5)
            else:
                # Run indefinitely until interrupted
                detector.start_monitoring()
        except KeyboardInterrupt:
            print(f"\nMotion detection system stopped by user at {now_pst().strftime('%H:%M:%S %Z')}.")
            detector.stop_monitoring()

def create_system(duration: int = 0):
    """Create a motion system with the specified duration."""
    return MotionSystem(duration)

def main():
    parser = argparse.ArgumentParser(description='Motion detection system')
    parser.add_argument('--duration', type=int, default=0, help='Duration to run in seconds (0 = indefinite)')
    args = parser.parse_args()

    system = create_system(args.duration)
    system.run()

if __name__ == "__main__":
    main()
