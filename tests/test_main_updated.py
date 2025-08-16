import pytest
from unittest.mock import Mock, patch, MagicMock
import threading
import datetime
from src.main import MotionSystem, create_system, main
from src.timezone_utils import now_pst

class TestMotionSystem:
    """Test suite for the updated MotionSystem class."""

    def test_motion_system_initialization_default(self):
        """Test MotionSystem initialization with default duration."""
        system = MotionSystem()
        assert system.duration == 0

    def test_motion_system_initialization_with_duration(self):
        """Test MotionSystem initialization with specific duration."""
        system = MotionSystem(duration=300)
        assert system.duration == 300

    @patch('src.main.MotionSensor')
    @patch('src.main.MotionEventDao')  
    @patch('src.main.MotionDetector')
    def test_create_components(self, mock_detector, mock_dao, mock_sensor):
        """Test creation of motion system components."""
        system = MotionSystem()
        
        mock_sensor_instance = Mock()
        mock_dao_instance = Mock()
        mock_detector_instance = Mock()
        
        mock_sensor.return_value = mock_sensor_instance
        mock_dao.return_value = mock_dao_instance
        mock_detector.return_value = mock_detector_instance
        
        sensor, database, detector = system.create_components()
        
        # Verify components were created with correct parameters
        mock_sensor.assert_called_once_with(4)  # GPIO pin 4
        mock_dao.assert_called_once()
        mock_detector.assert_called_once_with(mock_sensor_instance, mock_dao_instance)
        
        assert sensor == mock_sensor_instance
        assert database == mock_dao_instance
        assert detector == mock_detector_instance

    @patch('src.main.now_pst')
    def test_run_with_duration(self, mock_now_pst):
        """Test running motion system with specific duration."""
        system = MotionSystem(duration=5)
        
        # Mock PST time
        mock_time = Mock()
        mock_time.strftime.return_value = "2025-08-14 15:30:45 PDT"
        mock_now_pst.return_value = mock_time
        
        with patch.object(system, 'create_components') as mock_create, \
             patch('threading.Thread') as mock_thread, \
             patch('time.sleep') as mock_sleep, \
             patch('builtins.print') as mock_print:
            
            # Setup mocks
            mock_detector = Mock()
            mock_create.return_value = (Mock(), Mock(), mock_detector)
            
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            system.run()
            
            # Verify PST time logging
            mock_print.assert_any_call("Starting motion detection system at 2025-08-14 15:30:45 PDT...")
            
            # Verify sensor stabilization
            mock_detector.wait_for_sensor_ready.assert_called_once()
            
            # Verify threading setup
            mock_thread.assert_called_once_with(target=mock_detector.start_monitoring)
            mock_thread_instance.start.assert_called_once()
            
            # Verify duration timing - there are two sleep calls: duration + 0.5
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(5)
            mock_sleep.assert_any_call(0.5)
            mock_detector.stop_monitoring.assert_called_once()

    @patch('src.main.now_pst')
    def test_run_indefinite(self, mock_now_pst):
        """Test running motion system indefinitely (duration=0)."""
        system = MotionSystem(duration=0)
        
        mock_time = Mock()
        mock_time.strftime.return_value = "2025-08-14 15:30:45 PDT"
        mock_now_pst.return_value = mock_time
        
        with patch.object(system, 'create_components') as mock_create:
            mock_detector = Mock()
            mock_create.return_value = (Mock(), Mock(), mock_detector)
            
            system.run()
            
            # Should call start_monitoring directly (no threading)
            mock_detector.start_monitoring.assert_called_once()

    @patch('src.main.now_pst')
    def test_run_keyboard_interrupt(self, mock_now_pst):
        """Test handling keyboard interrupt during run."""
        system = MotionSystem(duration=60)
        
        mock_time = Mock()
        mock_time.strftime.return_value = "2025-08-14 15:30:45 PDT"
        mock_now_pst.return_value = mock_time
        
        with patch.object(system, 'create_components') as mock_create, \
             patch('threading.Thread') as mock_thread, \
             patch('time.sleep') as mock_sleep, \
             patch('builtins.print') as mock_print:
            
            mock_detector = Mock()
            mock_create.return_value = (Mock(), Mock(), mock_detector)
            
            # Simulate KeyboardInterrupt during sleep
            mock_sleep.side_effect = KeyboardInterrupt()
            
            system.run()
            
            # Should handle interrupt gracefully
            mock_print.assert_any_call("\nMotion detection system stopped by user at 2025-08-14 15:30:45 PDT.")
            mock_detector.stop_monitoring.assert_called_once()

    @patch('src.main.now_pst')
    def test_run_completion_logging(self, mock_now_pst):
        """Test completion logging with PST timestamp."""
        system = MotionSystem(duration=10)
        
        # Mock different PST times for start and end
        start_time = Mock()
        start_time.strftime.return_value = "2025-08-14 15:30:45 PDT"
        end_time = Mock() 
        end_time.strftime.return_value = "15:30:55 PDT"  # Shorter format used in completion message
        mock_now_pst.side_effect = [start_time, end_time]
        
        with patch.object(system, 'create_components') as mock_create, \
             patch('threading.Thread'), \
             patch('time.sleep'), \
             patch('builtins.print') as mock_print:
            
            mock_detector = Mock()
            mock_create.return_value = (Mock(), Mock(), mock_detector)
            
            system.run()
            
            # Verify completion message with PST time (shorter format)
            mock_print.assert_any_call("\nMotion detection completed after 10 seconds at 15:30:55 PDT.")

class TestCreateSystem:
    """Test the create_system factory function."""

    def test_create_system_default(self):
        """Test creating system with default duration."""
        system = create_system()
        assert isinstance(system, MotionSystem)
        assert system.duration == 0

    def test_create_system_with_duration(self):
        """Test creating system with specific duration."""
        system = create_system(300)
        assert isinstance(system, MotionSystem)
        assert system.duration == 300

class TestMainFunction:
    """Test the main command-line interface."""

    @patch('src.main.create_system')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_with_duration_arg(self, mock_parse_args, mock_create_system):
        """Test main function with duration argument."""
        # Mock command line arguments
        mock_args = Mock()
        mock_args.duration = 120
        mock_parse_args.return_value = mock_args
        
        # Mock system creation and running
        mock_system = Mock()
        mock_create_system.return_value = mock_system
        
        main()
        
        # Verify system was created with correct duration and run
        mock_create_system.assert_called_once_with(120)
        mock_system.run.assert_called_once()

    @patch('src.main.create_system')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_with_default_duration(self, mock_parse_args, mock_create_system):
        """Test main function with default duration."""
        # Mock command line arguments with default duration
        mock_args = Mock()
        mock_args.duration = 0  # Default value
        mock_parse_args.return_value = mock_args
        
        mock_system = Mock()
        mock_create_system.return_value = mock_system
        
        main()
        
        # Verify system was created with default duration
        mock_create_system.assert_called_once_with(0)
        mock_system.run.assert_called_once()

    @patch('argparse.ArgumentParser')
    def test_argument_parser_setup(self, mock_parser_class):
        """Test that argument parser is configured correctly."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        
        # Mock parse_args to avoid actually parsing
        mock_parser.parse_args.return_value = Mock(duration=0)
        
        with patch('src.main.create_system') as mock_create_system:
            mock_create_system.return_value = Mock()
            main()
        
        # Verify parser was configured with correct description and argument
        mock_parser_class.assert_called_once_with(description='Motion detection system')
        mock_parser.add_argument.assert_called_once_with(
            '--duration', 
            type=int, 
            default=0, 
            help='Duration to run in seconds (0 = indefinite)'
        )

class TestMotionSystemIntegration:
    """Integration tests for MotionSystem with real components (mocked)."""

    @patch('src.main.MotionSensor')
    @patch('src.main.MotionEventDao')
    @patch('src.main.MotionDetector')
    @patch('src.main.now_pst')
    def test_full_motion_detection_cycle(self, mock_now_pst, mock_detector_class, 
                                        mock_dao_class, mock_sensor_class):
        """Test complete motion detection cycle."""
        # Setup mocks
        mock_sensor = Mock()
        mock_dao = Mock()
        mock_detector = Mock()
        
        mock_sensor_class.return_value = mock_sensor
        mock_dao_class.return_value = mock_dao
        mock_detector_class.return_value = mock_detector
        
        mock_time = Mock()
        mock_time.strftime.return_value = "2025-08-14 15:30:45 PDT"
        mock_now_pst.return_value = mock_time
        
        # Create and run system
        system = MotionSystem(duration=1)
        
        with patch('threading.Thread') as mock_thread, \
             patch('time.sleep'):
            
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            system.run()
            
            # Verify complete workflow
            mock_sensor_class.assert_called_once_with(4)
            mock_dao_class.assert_called_once()
            mock_detector_class.assert_called_once_with(mock_sensor, mock_dao)
            mock_detector.wait_for_sensor_ready.assert_called_once()
            mock_detector.stop_monitoring.assert_called_once()

    def test_motion_system_thread_daemon_property(self):
        """Test that monitoring thread is set as daemon."""
        system = MotionSystem(duration=5)
        
        with patch.object(system, 'create_components') as mock_create, \
             patch('threading.Thread') as mock_thread, \
             patch('time.sleep'), \
             patch('src.main.now_pst'):
            
            mock_create.return_value = (Mock(), Mock(), Mock())
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            system.run()
            
            # Verify thread daemon property is set
            assert mock_thread_instance.daemon is True

    @patch('src.main.now_pst')
    def test_motion_system_cleanup_on_exception(self, mock_now_pst):
        """Test that system cleans up properly on exceptions."""
        system = MotionSystem(duration=5)
        
        mock_time = Mock()
        mock_time.strftime.return_value = "2025-08-14 15:30:45 PDT"
        mock_now_pst.return_value = mock_time
        
        with patch.object(system, 'create_components') as mock_create:
            mock_detector = Mock()
            mock_detector.wait_for_sensor_ready.side_effect = Exception("Sensor error")
            mock_create.return_value = (Mock(), Mock(), mock_detector)
            
            with pytest.raises(Exception, match="Sensor error"):
                system.run()
            
            # Should still attempt to call wait_for_sensor_ready
            mock_detector.wait_for_sensor_ready.assert_called_once()
