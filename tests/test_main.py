import pytest
from unittest.mock import Mock, patch
from src.main import MotionSystem, create_system, main

@pytest.fixture
def mock_components():
    motion_sensor = Mock()
    database = Mock()
    detector = Mock()
    return motion_sensor, database, detector

@pytest.fixture
def motion_system(mock_components):
    motion_sensor, database, detector = mock_components
    return MotionSystem(motion_sensor, database, detector)

def test_motion_system_initialization(mock_components):
    motion_sensor, database, detector = mock_components
    system = MotionSystem(motion_sensor, database, detector)
    
    assert system.motion_sensor == motion_sensor
    assert system.database == database
    assert system.detector == detector

def test_motion_system_run_with_duration(motion_system, mock_components):
    motion_sensor, database, detector = mock_components
    with patch('time.sleep') as mock_sleep:
        motion_system.run(3)  # Run for 3 seconds
        
        # Should call wait_for_sensor_ready and then start monitoring
        detector.wait_for_sensor_ready.assert_called_once()
        detector.start_monitoring.assert_called_once()
        detector.stop_monitoring.assert_called_once()
        mock_sleep.assert_any_call(3)  # Duration sleep
        mock_sleep.assert_any_call(0.5)  # Final cleanup sleep

def test_motion_system_run_keyboard_interrupt(motion_system, mock_components):
    motion_sensor, database, detector = mock_components
    with patch('time.sleep') as mock_sleep:
        # KeyboardInterrupt during duration sleep (first sleep call)
        mock_sleep.side_effect = [KeyboardInterrupt()]
        
        # Track call order using a list
        calls = []
        def track_start():
            calls.append('start')
        def track_stop():
            calls.append('stop')
            
        detector.start_monitoring.side_effect = track_start
        detector.stop_monitoring.side_effect = track_stop
        
        motion_system.run(3)  # Run for 3 seconds
        
        # Verify KeyboardInterrupt was handled
        assert mock_sleep.call_count == 1, "Should call sleep once before interrupt"
        assert mock_sleep.call_args_list[0].args == (3,), "First call should be duration (3s)"
        
        # Should call wait_for_sensor_ready
        detector.wait_for_sensor_ready.assert_called_once()
        assert detector.start_monitoring.call_count == 1, "Should start monitoring exactly once"
        assert detector.stop_monitoring.call_count == 1, "Should stop monitoring exactly once"
        # Verify call order
        assert calls == ['start', 'stop'], "Start monitoring should be called before stop monitoring"

def test_create_system():
    with patch('src.main.MotionSensor') as mock_sensor_cls, \
         patch('src.main.MotionEventDao') as mock_db_cls, \
         patch('src.main.MotionDetector') as mock_detector_cls:
        
        system = create_system()
        
        mock_sensor_cls.assert_called_once_with(4)
        mock_db_cls.assert_called_once()
        mock_detector_cls.assert_called_once()
        assert isinstance(system, MotionSystem)

def test_main_argument_parsing():
    test_args = ['main.py', '60']
    with patch('sys.argv', test_args), patch('src.main.create_system') as mock_create_system:
        
        mock_system = Mock()
        mock_create_system.return_value = mock_system
        
        main()
        
        mock_create_system.assert_called_once()
        mock_system.run.assert_called_once_with(60)
