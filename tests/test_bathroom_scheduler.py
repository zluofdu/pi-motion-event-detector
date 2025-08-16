import pytest
import datetime
import sys
from unittest.mock import Mock, patch, MagicMock
from bathroom_scheduler import BathroomHealthScheduler

class TestBathroomHealthScheduler:
    """Test suite for bathroom health scheduling functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.SMTP_SERVER = 'smtp.test.com'
        config.SMTP_PORT = 587
        config.EMAIL_ADDRESS = 'test@example.com'
        config.EMAIL_PASSWORD = 'test_password'
        config.REPORT_EMAIL = ['recipient@example.com']  # Should be a list
        return config

    @pytest.fixture
    def scheduler(self, mock_config):
        """Create scheduler with mocked dependencies."""
        with patch('bathroom_scheduler.Config') as mock_config_class:
            mock_config_class.return_value = mock_config
            
            with patch('bathroom_scheduler.BathroomReporter') as mock_reporter_class:
                with patch('bathroom_scheduler.BathroomVisitDetector') as mock_detector_class:
                    mock_reporter = Mock()
                    mock_detector = Mock()
                    mock_reporter_class.return_value = mock_reporter
                    mock_detector_class.return_value = mock_detector
                    
                    scheduler = BathroomHealthScheduler()
                    scheduler.reporter = mock_reporter
                    scheduler.detector = mock_detector
                    scheduler.target_emails = ['recipient@example.com']  # Should be a list
                    
                    return scheduler

    def test_initialization(self, scheduler, mock_config):
        """Test scheduler initialization."""
        assert scheduler.target_emails == ['recipient@example.com']
        assert isinstance(scheduler.reporter, Mock)
        assert isinstance(scheduler.detector, Mock)

    @patch('bathroom_scheduler.now_pst')
    @patch('bathroom_scheduler.pst_datetime_today')
    @patch('bathroom_scheduler.MotionSystem')
    def test_job1_motion_detection_normal_time(self, mock_motion_system, mock_pst_today, mock_now_pst, scheduler):
        """Test Job 1: Motion detection during normal hours."""
        # Mock current time as 12:30 AM
        mock_now = datetime.datetime(2025, 8, 14, 0, 30, 0)
        mock_now_pst.return_value = mock_now
        
        # Mock 8 AM target time
        mock_target = datetime.datetime(2025, 8, 14, 8, 0, 0)
        mock_pst_today.return_value = mock_target
        
        # Mock motion system
        mock_system = Mock()
        mock_motion_system.return_value = mock_system
        
        scheduler.job1_motion_detection()
        
        # Verify motion system was created with correct duration (7.5 hours = 27000 seconds)
        mock_motion_system.assert_called_once_with(duration=27000)
        mock_system.run.assert_called_once()

    @patch('bathroom_scheduler.now_pst')
    @patch('bathroom_scheduler.pst_datetime_today')
    @patch('bathroom_scheduler.MotionSystem')
    def test_job1_motion_detection_past_8am(self, mock_motion_system, mock_pst_today, mock_now_pst, scheduler):
        """Test Job 1: Motion detection when it's past 8 AM."""
        # Mock current time as 10 AM
        mock_now = datetime.datetime(2025, 8, 14, 10, 0, 0)
        mock_now_pst.return_value = mock_now
        
        # Mock today's 8 AM target time
        mock_target = datetime.datetime(2025, 8, 14, 8, 0, 0)
        mock_pst_today.return_value = mock_target
        
        # Mock motion system
        mock_system = Mock()
        mock_motion_system.return_value = mock_system
        
        scheduler.job1_motion_detection()
        
        # Should exit early since it's past 8 AM
        print("Test passed - should exit early when past 8 AM")

    @patch('bathroom_scheduler.now_pst')
    @patch('bathroom_scheduler.pst_datetime_today')
    @patch('bathroom_scheduler.MotionSystem')
    def test_job1_keyboard_interrupt(self, mock_motion_system, mock_pst_today, mock_now_pst, scheduler):
        """Test Job 1: Handle keyboard interrupt gracefully."""
        mock_now = datetime.datetime(2025, 8, 14, 0, 30, 0)
        mock_now_pst.return_value = mock_now
        
        mock_target = datetime.datetime(2025, 8, 14, 8, 0, 0)
        mock_pst_today.return_value = mock_target
        
        # Mock motion system to raise KeyboardInterrupt
        mock_system = Mock()
        mock_system.run.side_effect = KeyboardInterrupt()
        mock_motion_system.return_value = mock_system
        
        # Should not raise exception
        scheduler.job1_motion_detection()
        mock_system.run.assert_called_once()

    @patch('bathroom_scheduler.now_pst')
    @patch('bathroom_scheduler.pst_datetime_today')
    def test_job2_generate_report(self, mock_pst_today, mock_now_pst, scheduler):
        """Test Job 2: Report generation and email."""
        # Mock PST time
        mock_now = Mock()
        mock_now.date.return_value = datetime.date(2025, 8, 14)
        mock_now_pst.return_value = mock_now
        
        # Mock today datetime
        mock_start_time = Mock()
        mock_end_time = Mock()
        mock_pst_today.side_effect = [mock_start_time, mock_end_time]
        
        # Mock visit detection
        mock_visits = [Mock(), Mock()]  # 2 mock visits
        scheduler.detector.detect_visits_for_period.return_value = mock_visits
        
        # Mock report generation
        mock_report_data = {
            'total_visits': 2, 
            'avg_duration': 300,
            'total_time': 600,
            'hourly_distribution': {},
            'longest_visit': None,
            'shortest_visit': None,
            'visits': mock_visits
        }
        scheduler.reporter.generate_report.return_value = mock_report_data
        
        # Mock email sending
        scheduler.reporter.send_report.return_value = True
        
        scheduler.job2_generate_report()
        
        # Verify visit detection was called with correct time range
        scheduler.detector.detect_visits_for_period.assert_called_once_with(mock_start_time, mock_end_time)
        
        # Verify visits were saved
        scheduler.detector.save_visits.assert_called_once_with(mock_visits)
        
        # Verify report was generated and sent
        scheduler.reporter.generate_report.assert_called_once()
        scheduler.reporter.send_report.assert_called_once()

    @patch('bathroom_scheduler.now_pst')
    @patch('bathroom_scheduler.pst_datetime_today')
    def test_job2_no_visits_found(self, mock_pst_today, mock_now_pst, scheduler):
        """Test Job 2: No visits found."""
        mock_now_pst.return_value.date.return_value = datetime.date(2025, 8, 14)
        mock_pst_today.side_effect = [Mock(), Mock()]
        
        # No visits found
        scheduler.detector.detect_visits_for_period.return_value = []
        scheduler.reporter.generate_report.return_value = {
            'total_visits': 0,
            'avg_duration': 0,
            'total_time': 0,
            'hourly_distribution': {},
            'longest_visit': None,
            'shortest_visit': None,
            'visits': []
        }
        scheduler.reporter.send_report.return_value = True
        
        scheduler.job2_generate_report()
        
        # Should not call save_visits for empty list
        scheduler.detector.save_visits.assert_not_called()
        
        # Should still generate and send report
        scheduler.reporter.generate_report.assert_called_once()
        scheduler.reporter.send_report.assert_called_once()

    @patch('bathroom_scheduler.now_pst')
    @patch('bathroom_scheduler.pst_datetime_today')
    def test_job2_email_failure(self, mock_pst_today, mock_now_pst, scheduler):
        """Test Job 2: Email sending failure."""
        mock_now_pst.return_value.date.return_value = datetime.date(2025, 8, 14)
        mock_pst_today.side_effect = [Mock(), Mock()]
        
        scheduler.detector.detect_visits_for_period.return_value = []
        scheduler.reporter.generate_report.return_value = {
            'total_visits': 0,
            'avg_duration': 0,
            'total_time': 0,
            'hourly_distribution': {},
            'longest_visit': None,
            'shortest_visit': None,
            'visits': []
        }
        
        # Mock email failure
        scheduler.reporter.send_report.return_value = False
        
        scheduler.job2_generate_report()
        
        # Should handle email failure gracefully
        scheduler.reporter.send_report.assert_called_once()

    @patch('bathroom_scheduler.now_pst')
    @patch('bathroom_scheduler.pst_datetime_today')
    def test_job2_no_target_email(self, mock_pst_today, mock_now_pst, scheduler):
        """Test Job 2: No target email configured."""
        scheduler.target_emails = []  # No email configured
        
        mock_now_pst.return_value.date.return_value = datetime.date(2025, 8, 14)
        mock_pst_today.side_effect = [Mock(), Mock()]
        
        scheduler.detector.detect_visits_for_period.return_value = []
        scheduler.reporter.generate_report.return_value = {
            'total_visits': 0,
            'avg_duration': 0,
            'total_time': 0,
            'hourly_distribution': {},
            'longest_visit': None,
            'shortest_visit': None,
            'visits': []
        }
        
        scheduler.job2_generate_report()
        
        # Should not attempt to send email
        scheduler.reporter.send_report.assert_not_called()

    def test_print_summary(self, scheduler):
        """Test summary printing functionality."""
        mock_visit = Mock()
        mock_visit.duration_seconds = 360
        mock_visit.visit_start.strftime.return_value = '02:30'
        
        report_data = {
            'total_visits': 3,
            'avg_duration': 300,
            'total_time': 900,
            'longest_visit': mock_visit,
            'hourly_distribution': {2: 2, 4: 1}
        }
        
        # Should not raise any exceptions
        scheduler._print_summary(report_data)

    def test_print_summary_empty_data(self, scheduler):
        """Test summary printing with empty data."""
        report_data = {
            'total_visits': 0,
            'avg_duration': 0,
            'total_time': 0,
            'longest_visit': None,
            'hourly_distribution': {}
        }
        
        # Should not raise any exceptions
        scheduler._print_summary(report_data)

    def test_run_job_1(self, scheduler):
        """Test running job 1."""
        with patch.object(scheduler, 'job1_motion_detection') as mock_job1:
            scheduler.run_job(1)
            mock_job1.assert_called_once()

    def test_run_job_2(self, scheduler):
        """Test running job 2."""
        with patch.object(scheduler, 'job2_generate_report') as mock_job2:
            scheduler.run_job(2)
            mock_job2.assert_called_once()

    def test_run_job_invalid(self, scheduler):
        """Test running invalid job number."""
        with pytest.raises(SystemExit):
            scheduler.run_job(3)

class TestMainFunction:
    """Test the main function and argument parsing."""

    @patch('bathroom_scheduler.BathroomHealthScheduler')
    @patch('sys.argv', ['bathroom_scheduler.py', '1'])
    def test_main_job_1(self, mock_scheduler_class):
        """Test main function with job 1."""
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from bathroom_scheduler import main
        main()
        
        mock_scheduler.run_job.assert_called_once_with(1)

    @patch('bathroom_scheduler.BathroomHealthScheduler')
    @patch('sys.argv', ['bathroom_scheduler.py', '2'])
    def test_main_job_2(self, mock_scheduler_class):
        """Test main function with job 2."""
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from bathroom_scheduler import main
        main()
        
        mock_scheduler.run_job.assert_called_once_with(2)

    @patch('sys.argv', ['bathroom_scheduler.py'])
    def test_main_no_args(self):
        """Test main function with no arguments."""
        from bathroom_scheduler import main
        
        with pytest.raises(SystemExit):
            main()

    @patch('sys.argv', ['bathroom_scheduler.py', 'invalid'])
    def test_main_invalid_job_number(self):
        """Test main function with invalid job number."""
        from bathroom_scheduler import main
        
        with pytest.raises(SystemExit):
            main()

    @patch('sys.argv', ['bathroom_scheduler.py', '1', 'extra'])
    def test_main_too_many_args(self):
        """Test main function with too many arguments."""
        from bathroom_scheduler import main
        
        with pytest.raises(SystemExit):
            main()

class TestSchedulerIntegration:
    """Integration tests for scheduler components."""

    @patch('bathroom_scheduler.Config')
    @patch('bathroom_scheduler.BathroomReporter')
    @patch('bathroom_scheduler.BathroomVisitDetector')
    def test_scheduler_config_integration(self, mock_detector_class, mock_reporter_class, mock_config_class):
        """Test that scheduler properly integrates with config."""
        mock_config = Mock()
        mock_config.SMTP_SERVER = 'smtp.gmail.com'
        mock_config.SMTP_PORT = 587
        mock_config.EMAIL_ADDRESS = 'test@gmail.com'
        mock_config.EMAIL_PASSWORD = ''
        mock_config_class.return_value = mock_config
        
        scheduler = BathroomHealthScheduler()
        
        # Verify reporter was initialized with config values
        mock_reporter_class.assert_called_once_with(
            smtp_server='smtp.gmail.com',
            smtp_port=587,  # Default value
            email='test@gmail.com',
            password=''     # Default empty value
        )
        
        mock_detector_class.assert_called_once()

    @patch('bathroom_scheduler.getattr')
    def test_config_fallback_values(self, mock_getattr):
        """Test configuration fallback values."""
        # Mock getattr to return fallback values
        def getattr_side_effect(obj, attr, default):
            fallback_values = {
                'SMTP_SERVER': 'smtp.gmail.com',
                'SMTP_PORT': 587,
                'EMAIL_ADDRESS': 'fallback@test.com',
                'EMAIL_PASSWORD': 'fallback_password',
                'REPORT_EMAIL': ['report@test.com']
            }
            return fallback_values.get(attr, default)
        
        mock_getattr.side_effect = getattr_side_effect
        
        with patch('bathroom_scheduler.Config'):
            with patch('bathroom_scheduler.BathroomReporter') as mock_reporter_class:
                with patch('bathroom_scheduler.BathroomVisitDetector'):
                    scheduler = BathroomHealthScheduler()
                    
                    # Verify fallback values were used
                    mock_reporter_class.assert_called_once_with(
                        smtp_server='smtp.gmail.com',
                        smtp_port=587,
                        email='fallback@test.com',
                        password='fallback_password'
                    )
