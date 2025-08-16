import pytest
from unittest.mock import Mock, patch
import datetime
from src.motion_detector import MotionDetector
from src.models.motion_event import MotionEvent
from src.timezone_utils import now_pst, pst_from_naive

@pytest.fixture
def mock_components():
    sensor = Mock()
    # Setup the pin mock to simulate GPIO pin
    sensor.pin = Mock()
    sensor.pin.__str__ = Mock(return_value="GPIO4")
    
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

def test_wait_for_sensor_ready(detector, mock_components):
    sensor, database = mock_components
    
    # Mock sensor values to be stable (same value consistently)
    sensor.value = 0  # Sensor shows no motion initially
    
    with patch('time.sleep') as mock_sleep, \
         patch('time.time') as mock_time, \
         patch('builtins.print') as mock_print:
        
        # Mock time to avoid actual timeout
        mock_time.side_effect = [0, 1, 2, 3, 4, 5]  # Simulate time progression
        
        detector.wait_for_sensor_ready()
        
        # Should have called sleep for small delays between readings
        assert mock_sleep.call_count >= 5  # At least 5 readings
        mock_sleep.assert_called_with(0.1)
        
        # Should print status messages
        mock_print.assert_any_call("Checking sensor status...")
        mock_print.assert_any_call("Sensor is ready!")

def test_wait_for_sensor_ready_with_timeout(detector, mock_components):
    sensor, database = mock_components
    
    # Mock sensor values to be unstable (changing values)
    sensor.value = Mock(side_effect=[0, 1, 0, 1, 0, 1, 0])  # Alternating values
    
    with patch('time.sleep') as mock_sleep, \
         patch('time.time') as mock_time, \
         patch('builtins.print') as mock_print:
        
        # Mock time to trigger timeout after 11 seconds
        mock_time.side_effect = [0, 5, 11]  # Start, during, timeout
        
        detector.wait_for_sensor_ready()
        
        # Should print timeout message
        mock_print.assert_any_call("Sensor stabilization timeout reached, proceeding anyway...")

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

def test_capture_motion_event_pst_timestamps(detector, mock_components):
    """Test that motion events are captured with PST timestamps."""
    sensor, database = mock_components
    
    with patch('src.motion_detector.now_pst') as mock_now_pst:
        # Setup mock PST times
        start_time_pst = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 30, 0))
        stop_time_pst = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 30, 10))
        mock_now_pst.side_effect = [start_time_pst, stop_time_pst]
        
        # Set detector to running state
        detector._running = True
        
        detector.capture_motion_event()
        
        # Verify PST times were used
        mock_now_pst.assert_called()
        assert mock_now_pst.call_count == 2
        
        # Verify event was created with PST timestamps
        database.add.assert_called_once()
        event = database.add.call_args[0][0]
        assert event.device_id == "pir_sensor_GPIO4"
        assert event.start_timestamp == start_time_pst
        assert event.stop_timestamp == stop_time_pst
        
        # Verify timestamps are timezone-aware
        assert event.start_timestamp.tzinfo is not None
        assert event.stop_timestamp.tzinfo is not None
        assert event.start_timestamp.tzinfo.zone == 'US/Pacific'

def test_capture_motion_event_pst_logging(detector, mock_components):
    """Test that motion detection logging displays PST timezone."""
    sensor, database = mock_components
    
    with patch('src.motion_detector.now_pst') as mock_now_pst, \
         patch('builtins.print') as mock_print:
        
        # Setup mock PST times
        start_time_pst = pst_from_naive(datetime.datetime(2025, 8, 14, 15, 30, 45))
        stop_time_pst = pst_from_naive(datetime.datetime(2025, 8, 14, 15, 30, 55))
        mock_now_pst.side_effect = [start_time_pst, stop_time_pst]
        
        detector._running = True
        detector.capture_motion_event()
        
        # Verify PST timezone is displayed in logs
        mock_print.assert_any_call("Motion detected at 2025-08-14 15:30:45 PDT")
        mock_print.assert_any_call("Motion stopped at 2025-08-14 15:30:55 PDT")

def test_capture_motion_event_interrupted_during_start(detector, mock_components):
    """Test handling interruption during motion start detection."""
    sensor, database = mock_components
    
    # Set running to False after wait_for_motion (simulating stop)
    def stop_after_motion_start(*args):
        detector._running = False
    
    sensor.wait_for_motion.side_effect = stop_after_motion_start
    
    detector._running = True
    detector.capture_motion_event()
    
    # Should return early without recording event
    sensor.wait_for_no_motion.assert_not_called()
    database.add.assert_not_called()

def test_capture_motion_event_interrupted_during_stop(detector, mock_components):
    """Test handling interruption during motion stop detection."""
    sensor, database = mock_components
    
    with patch('src.motion_detector.now_pst') as mock_now_pst:
        # Setup first timestamp
        start_time_pst = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 30, 0))
        mock_now_pst.return_value = start_time_pst
        
        # Set running to False after wait_for_no_motion (simulating stop)
        def stop_after_motion_end(*args):
            detector._running = False
        
        sensor.wait_for_no_motion.side_effect = stop_after_motion_end
        
        detector._running = True
        detector.capture_motion_event()
        
        # Should get first timestamp but return early before recording
        sensor.wait_for_motion.assert_called_once()
        sensor.wait_for_no_motion.assert_called_once()
        database.add.assert_not_called()

def test_device_id_generation_from_pin(mock_components):
    """Test that device ID is properly generated from GPIO pin."""
    sensor, database = mock_components
    
    # Test different pin configurations
    test_cases = [
        ("GPIO4", "pir_sensor_GPIO4"),
        ("4", "pir_sensor_4"),
        ("BOARD7", "pir_sensor_BOARD7"),
    ]
    
    for pin_str, expected_device_id in test_cases:
        sensor.pin.__str__.return_value = pin_str
        detector = MotionDetector(sensor, database)
        assert detector.device_id == expected_device_id
