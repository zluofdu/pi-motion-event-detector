import pytest
import datetime
from unittest.mock import Mock, patch, MagicMock
from src.bathroom_reporter import BathroomReporter
from src.models.bathroom_visit import BathroomVisit
from src.timezone_utils import pst_from_naive

class TestBathroomReporter:
    """Test suite for bathroom reporting functionality."""

    @pytest.fixture
    def reporter(self):
        """Create reporter instance for testing."""
        return BathroomReporter(
            smtp_server='smtp.test.com',
            smtp_port=587,
            email='test@example.com',
            password='test_password'
        )

    @pytest.fixture
    def sample_visits(self):
        """Create sample bathroom visits for testing."""
        base_time = datetime.datetime(2025, 8, 14, 2, 0)
        
        visits = []
        for i in range(3):
            start_time = base_time + datetime.timedelta(hours=i*2)
            end_time = start_time + datetime.timedelta(minutes=5)
            
            visit = BathroomVisit(
                device_id='pir_sensor_4',
                visit_start=pst_from_naive(start_time),
                visit_end=pst_from_naive(end_time),
                event_count=2 + i,
                duration_seconds=300 + i*60  # 5-7 minutes
            )
            visits.append(visit)
        
        return visits

    def test_initialization(self, reporter):
        """Test reporter initialization."""
        assert reporter.smtp_server == 'smtp.test.com'
        assert reporter.smtp_port == 587
        assert reporter.email == 'test@example.com'
        assert reporter.password == 'test_password'

    def test_generate_report_empty_visits(self, reporter):
        """Test report generation with no visits."""
        report_date = datetime.date(2025, 8, 14)
        report_data = reporter.generate_report([], report_date)
        
        assert report_data['total_visits'] == 0
        assert report_data['avg_duration'] == 0
        assert report_data['total_time'] == 0
        assert report_data['hourly_distribution'] == {}
        assert report_data['longest_visit'] is None
        assert report_data['shortest_visit'] is None

    def test_generate_report_with_visits(self, reporter, sample_visits):
        """Test report generation with sample visits."""
        report_date = datetime.date(2025, 8, 14)
        report_data = reporter.generate_report(sample_visits, report_date)
        
        assert report_data['total_visits'] == 3
        assert report_data['avg_duration'] == 360  # (300+360+420)/3
        assert report_data['total_time'] == 1080   # 300+360+420
        
        # Check hourly distribution (visits at 2:00, 4:00, 6:00 PST)
        expected_hours = {2: 1, 4: 1, 6: 1}
        assert report_data['hourly_distribution'] == expected_hours
        
        # Check extremes
        assert report_data['longest_visit'].duration_seconds == 420
        assert report_data['shortest_visit'].duration_seconds == 300
        assert report_data['visits'] == sample_visits

    def test_generate_report_timezone_conversion(self, reporter):
        """Test that hourly distribution uses PST times."""
        # Create visits with different timezone info
        visits = [
            BathroomVisit(
                device_id='pir_sensor_4',
                visit_start=pst_from_naive(datetime.datetime(2025, 8, 14, 14, 30)),  # 2:30 PM PST
                visit_end=pst_from_naive(datetime.datetime(2025, 8, 14, 14, 35)),
                event_count=2,
                duration_seconds=300
            )
        ]
        
        report_data = reporter.generate_report(visits, datetime.date(2025, 8, 14))
        
        # Should group by PST hour (14 = 2 PM PST)
        assert 14 in report_data['hourly_distribution']
        assert report_data['hourly_distribution'][14] == 1

    def test_create_html_email_structure(self, reporter, sample_visits):
        """Test HTML email structure and content."""
        report_data = {
            'total_visits': 3,
            'avg_duration': 360,
            'total_time': 1080,
            'hourly_distribution': {2: 1, 4: 1, 6: 1},
            'longest_visit': sample_visits[2],
            'shortest_visit': sample_visits[0],
            'visits': sample_visits
        }
        
        report_date = datetime.date(2025, 8, 14)
        
        html = reporter.create_html_email(report_data, report_date)
        
        # Check basic HTML structure
        assert '<!DOCTYPE html>' in html
        assert '<html>' in html
        assert '</html>' in html
        
        # Check content elements
        assert 'Bathroom Visits' in html
        assert 'August 14, 2025' in html
        assert 'Total Visits: 3' in html  # Total visits in summary
        assert '5.0 min' in html  # Individual visit durations
        assert '6.0 min' in html
        assert '7.0 min' in html
        
        # Check PST references
        assert 'PST' in html

    @patch('src.bathroom_reporter.smtplib.SMTP')
    def test_send_report_success(self, mock_smtp, reporter, sample_visits):
        """Test successful email sending."""
        # Setup SMTP mock
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        report_data = reporter.generate_report(sample_visits, datetime.date(2025, 8, 14))
        
        result = reporter.send_report('recipient@test.com', report_data, datetime.date(2025, 8, 14))
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@example.com', 'test_password')
        mock_server.send_message.assert_called_once()

    @patch('src.bathroom_reporter.smtplib.SMTP')
    def test_send_report_failure(self, mock_smtp, reporter, sample_visits):
        """Test email sending failure."""
        # Setup SMTP mock to raise exception
        mock_smtp.side_effect = Exception('SMTP Error')
        
        report_data = reporter.generate_report(sample_visits, datetime.date(2025, 8, 14))
        result = reporter.send_report('recipient@test.com', report_data, datetime.date(2025, 8, 14))
        
        assert result is False

    def test_html_email_escaping(self, reporter):
        """Test that HTML content is properly escaped."""
        # Create visit with potentially problematic content
        visit = BathroomVisit(
            device_id='pir_sensor_<script>',  # Potential XSS
            visit_start=pst_from_naive(datetime.datetime(2025, 8, 14, 2, 0)),
            visit_end=pst_from_naive(datetime.datetime(2025, 8, 14, 2, 5)),
            event_count=2,
            duration_seconds=300
        )
        
        report_data = reporter.generate_report([visit], datetime.date(2025, 8, 14))
        html = reporter.create_html_email(report_data, datetime.date(2025, 8, 14))
        
        # Verify the content is safe (device_id shouldn't appear as raw HTML)
        assert '<script>' not in html
        
    def test_email_footer_pst_reference(self, reporter):
        """Test that email footer mentions PST timezone."""
        report_data = {
            'total_visits': 0,
            'avg_duration': 0,
            'total_time': 0,
            'hourly_distribution': {},
            'longest_visit': None,
            'shortest_visit': None,
            'visits': []
        }
        
        html = reporter.create_html_email(report_data, datetime.date(2025, 8, 14))
        
        assert 'Pacific Standard Time' in html
        assert 'PST/PDT' in html
        assert '12:30 AM - 8:00 AM PST' in html
