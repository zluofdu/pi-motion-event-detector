import pytest
from unittest.mock import Mock, patch
import datetime
from src.motion_detector import MotionDetector
from src.models.motion_event import MotionEvent

@pytest.fixture
def mock_components():
    sensor = Mock()
    # Setup the pin mock to simulate GPIO pin
    sensor.pin = Mock()
    sensor.pin.name = "GPIO4"
    
    database = Mock()
    return sensor, database

@pytest.fixture
def detector(mock_components):
    sensor, database = mock_components
    return MotionDetector(sensor, database)

def test_detector_initialization(mock_components):
    sensor, database = mock_components
    detector = MotionDetector(sensor, database)
    
    assert detector.sensor == sensor
    assert detector.database == database
    assert detector.device_id == "pir_sensor_GPIO4"
    assert detector._running is False

def test_start_and_stop_monitoring(detector, mock_components):
    sensor, database = mock_components
    
    # Setup a flag to control the monitoring loop
    def set_running_false(*args):
        detector._running = False
    
    # Make wait_for_motion call our function to stop the loop after first event
    sensor.wait_for_motion.side_effect = set_running_false
    
    detector.start_monitoring()
    
    # Should have tried to detect motion
    sensor.wait_for_motion.assert_called_once()
    # Should not have recorded an event since we stopped before motion ended
    database.add.assert_not_called()

def test_capture_complete_motion_event(detector, mock_components):
    sensor, database = mock_components
    
    with patch('datetime.datetime') as mock_datetime:
        # Setup mock times for start and stop
        start_time = datetime.datetime(2025, 8, 13, 15, 0, 0)
        stop_time = datetime.datetime(2025, 8, 13, 15, 0, 10)
        mock_datetime.now.side_effect = [start_time, stop_time]
        
        # Set detector to running state for the test
        detector._running = True
        
        # Capture one event
        detector.capture_motion_event()
        
        # Verify sensor interactions
        sensor.wait_for_motion.assert_called_once()
        sensor.wait_for_no_motion.assert_called_once()
        
        # Verify event was created and saved
        database.add.assert_called_once()
        saved_event = database.add.call_args[0][0]
        assert isinstance(saved_event, MotionEvent)
        assert saved_event.device_id == "pir_sensor_GPIO4"
        assert saved_event.start_timestamp == start_time
        assert saved_event.stop_timestamp == stop_time

def test_stop_during_motion_detection(detector, mock_components):
    sensor, database = mock_components
    
    def stop_detector(*args):
        detector.stop_monitoring()
    
    # Stop during motion detection
    sensor.wait_for_motion.side_effect = stop_detector
    
    detector.start_monitoring()
    
    # Should have tried to detect motion
    sensor.wait_for_motion.assert_called_once()
    # Should not have recorded any events
    database.add.assert_not_called()

def test_error_handling(detector, mock_components):
    sensor, database = mock_components
    
    # Simulate an error during motion detection
    sensor.wait_for_motion.side_effect = Exception("Sensor error")
    
    with pytest.raises(Exception, match="Sensor error"):
        detector.start_monitoring()
    
    assert detector._running is False  # Should clean up running state
    database.add.assert_not_called()  # Should not have saved any events
