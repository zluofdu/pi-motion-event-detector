import pytest
from unittest.mock import Mock, patch
from src.main import MotionSystem, create_system, main

def test_motion_system_initialization():
    """Test motion system initialization."""
    system = MotionSystem(duration=10)
    assert system.duration == 10

def test_motion_system_initialization_default():
    """Test motion system with default duration."""
    system = MotionSystem()
    assert system.duration == 0

@patch('src.main.MotionDetector')
@patch('src.main.MotionEventDao') 
@patch('src.main.MotionSensor')
def test_create_components(mock_sensor_cls, mock_dao_cls, mock_detector_cls):
    """Test component creation."""
    system = MotionSystem()
    
    mock_sensor = Mock()
    mock_dao = Mock()
    mock_detector = Mock()
    
    mock_sensor_cls.return_value = mock_sensor
    mock_dao_cls.return_value = mock_dao
    mock_detector_cls.return_value = mock_detector
    
    sensor, dao, detector = system.create_components()
    
    mock_sensor_cls.assert_called_once_with(4)
    mock_dao_cls.assert_called_once()
    mock_detector_cls.assert_called_once_with(mock_sensor, mock_dao)
    
    assert sensor == mock_sensor
    assert dao == mock_dao
    assert detector == mock_detector

@patch('src.main.MotionSystem.create_components')
def test_motion_system_run_with_duration(mock_create_components):
    """Test motion system run with duration."""
    # Setup mocks
    mock_sensor = Mock()
    mock_dao = Mock() 
    mock_detector = Mock()
    mock_create_components.return_value = (mock_sensor, mock_dao, mock_detector)
    
    system = MotionSystem(duration=3)
    
    with patch('time.sleep') as mock_sleep:
        system.run()
        
        # Should call wait_for_sensor_ready and then start monitoring
        mock_detector.wait_for_sensor_ready.assert_called_once()
        mock_detector.start_monitoring.assert_called_once()
        mock_detector.stop_monitoring.assert_called_once()
        mock_sleep.assert_any_call(3)  # Duration sleep
        mock_sleep.assert_any_call(0.5)  # Final cleanup sleep

@patch('src.main.MotionSystem.create_components')
def test_motion_system_run_keyboard_interrupt(mock_create_components):
    """Test motion system run with keyboard interrupt."""
    # Setup mocks
    mock_sensor = Mock()
    mock_dao = Mock() 
    mock_detector = Mock()
    mock_create_components.return_value = (mock_sensor, mock_dao, mock_detector)
    
    system = MotionSystem(duration=3)
    
    with patch('time.sleep') as mock_sleep:
        # KeyboardInterrupt during duration sleep (first sleep call)
        mock_sleep.side_effect = [KeyboardInterrupt()]
        
        system.run()
        
        # Should still call cleanup methods
        mock_detector.wait_for_sensor_ready.assert_called_once()
        mock_detector.start_monitoring.assert_called_once()
        mock_detector.stop_monitoring.assert_called_once()

def test_create_system():
    """Test the create_system function."""
    with patch('src.main.MotionSensor') as mock_sensor_cls, \
         patch('src.main.MotionEventDao') as mock_db_cls, \
         patch('src.main.MotionDetector') as mock_detector_cls:
        
        system = create_system()
        
        # Should be called when components are created, not during create_system
        assert isinstance(system, MotionSystem)

def test_main_argument_parsing():
    """Test main function argument parsing."""
    test_args = ['main.py', '--duration', '60']
    with patch('sys.argv', test_args), patch('src.main.create_system') as mock_create_system:
        
        mock_system = Mock()
        mock_create_system.return_value = mock_system
        
        main()
        
        mock_create_system.assert_called_once_with(60)
        mock_system.run.assert_called_once()
