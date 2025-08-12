from gpiozero import MotionSensor
from detector import MotionDetector
from database import MotionEventDao
import time

def main():
    # Initialize components
    motion_sensor = MotionSensor(4)
    database = MotionEventDao()
    detector = MotionDetector(motion_sensor, database)

    print("Starting motion detection system...")
    print("Waiting for sensor to settle...")
    time.sleep(2)  # Wait for the sensor to stabilize

    try:
        for _ in range(2):  # Run 2 iterations for testing
            print("Monitoring for motion...")
            detector.start_monitoring()
            time.sleep(1)  # Adjust sleep time as necessary

    except KeyboardInterrupt:
        print("\nMotion detection system stopped by user.")

if __name__ == "__main__":
    main()