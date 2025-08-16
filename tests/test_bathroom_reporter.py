import pytest
import datetime
import base64
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

    @patch('src.bathroom_reporter.plt')
    def test_create_charts_empty_data(self, mock_plt, reporter):
        """Test chart creation with no data."""
        report_data = {
            'total_visits': 0,
            'visits': []
        }
        
        result = reporter.create_charts(report_data)
        assert result == ""
        mock_plt.subplots.assert_not_called()

    @patch('src.bathroom_reporter.plt')
    @patch('src.bathroom_reporter.base64')
    @patch('src.bathroom_reporter.BytesIO')
    def test_create_charts_with_data(self, mock_bytesio, mock_base64, mock_plt, reporter, sample_visits):
        """Test chart creation with visit data."""
        # Setup mocks
        mock_fig = Mock()
        mock_axes = [[Mock(), Mock()], [Mock(), Mock()]]
        mock_plt.subplots.return_value = (mock_fig, mock_axes)
        
        # Mock the bar chart return value properly - it should be iterable
        mock_bars = [Mock(), Mock(), Mock()]  # Mock bars for iteration
        mock_axes[0][0].bar.return_value = mock_bars
        
        mock_buffer = Mock()
        mock_bytesio.return_value = mock_buffer
        mock_buffer.getvalue.return_value = b'fake_image_data'
        mock_base64.b64encode.return_value = b'encoded_data'
        
        report_data = {
            'total_visits': 3,
            'avg_duration': 360,
            'total_time': 1080,
            'hourly_distribution': {2: 1, 4: 1, 6: 1},
            'longest_visit': sample_visits[2],
            'shortest_visit': sample_visits[0],
            'visits': sample_visits
        }
        
        result = reporter.create_charts(report_data)
        
        # Verify chart creation was called
        mock_plt.subplots.assert_called_once_with(2, 2, figsize=(16, 12))
        mock_fig.suptitle.assert_called_once()
        
        # Verify image encoding
        mock_base64.b64encode.assert_called_once()
        assert result == 'encoded_data'

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
        
        chart_image = 'fake_base64_data'
        report_date = datetime.date(2025, 8, 14)
        
        html = reporter.create_html_email(report_data, chart_image, report_date)
        
        # Check basic HTML structure
        assert '<!DOCTYPE html>' in html
        assert '<html>' in html
        assert '</html>' in html
        
        # Check content elements
        assert 'Bathroom Visit Report' in html
        assert 'August 14, 2025' in html
        assert '3</div>' in html  # Total visits
        assert '6.0</div>' in html  # Avg duration (360/60 = 6.0 minutes)
        assert '18</div>' in html   # Total time (1080/60 = 18 minutes)
        
        # Check chart embedding
        assert f'data:image/png;base64,{chart_image}' in html
        
        # Check PST references
        assert 'PST' in html

    def test_create_html_email_health_status(self, reporter):
        """Test health status determination in email."""
        test_cases = [
            (6, 'Excellent', '#28a745'),
            (4, 'Good', '#ffc107'),
            (2, 'Fair', '#fd7e14'),
            (1, 'Concerning', '#dc3545')
        ]
        
        for visit_count, expected_status, expected_color in test_cases:
            visits = []
            for i in range(visit_count):
                visits.append(BathroomVisit(
                    device_id='test',
                    visit_start=pst_from_naive(datetime.datetime(2025, 8, 14, 2, 0)),
                    visit_end=pst_from_naive(datetime.datetime(2025, 8, 14, 2, 5)),
                    event_count=2,
                    duration_seconds=300
                ))
            
            report_data = reporter.generate_report(visits, datetime.date(2025, 8, 14))
            html = reporter.create_html_email(report_data, '', datetime.date(2025, 8, 14))
            
            assert expected_status in html
            assert expected_color in html

    def test_generate_recommendations_low_visits(self, reporter):
        """Test recommendations for low visit frequency."""
        report_data = {
            'total_visits': 1,
            'avg_duration': 300,
            'hourly_distribution': {}
        }
        
        recommendations = reporter._generate_recommendations(report_data)
        
        assert 'Low visit frequency' in recommendations
        assert 'increasing fluid intake' in recommendations

    def test_generate_recommendations_high_visits(self, reporter):
        """Test recommendations for high visit frequency."""
        report_data = {
            'total_visits': 10,
            'avg_duration': 300,
            'hourly_distribution': {}
        }
        
        recommendations = reporter._generate_recommendations(report_data)
        
        assert 'High visit frequency' in recommendations
        assert 'overhydration' in recommendations

    def test_generate_recommendations_long_duration(self, reporter):
        """Test recommendations for long visit duration."""
        report_data = {
            'total_visits': 5,
            'avg_duration': 720,  # 12 minutes
            'hourly_distribution': {}
        }
        
        recommendations = reporter._generate_recommendations(report_data)
        
        assert 'Extended visit duration' in recommendations
        assert 'digestive issues' in recommendations

    def test_generate_recommendations_peak_times(self, reporter):
        """Test recommendations based on peak hours."""
        test_cases = [
            ({1: 3}, 'Early night pattern'),
            ({7: 3}, 'Early morning pattern')
        ]
        
        for hourly_dist, expected_pattern in test_cases:
            report_data = {
                'total_visits': 3,
                'avg_duration': 300,
                'hourly_distribution': hourly_dist
            }
            
            recommendations = reporter._generate_recommendations(report_data)
            assert expected_pattern in recommendations

    @patch('src.bathroom_reporter.smtplib.SMTP')
    def test_send_report_success(self, mock_smtp, reporter, sample_visits):
        """Test successful email sending."""
        # Setup SMTP mock
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        report_data = reporter.generate_report(sample_visits, datetime.date(2025, 8, 14))
        
        with patch.object(reporter, 'create_charts', return_value='fake_chart'):
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
        
        with patch.object(reporter, 'create_charts', return_value='fake_chart'):
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
        html = reporter.create_html_email(report_data, '', datetime.date(2025, 8, 14))
        
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
        
        html = reporter.create_html_email(report_data, '', datetime.date(2025, 8, 14))
        
        assert 'Pacific Standard Time' in html
        assert 'PST/PDT' in html
        assert '12:30 AM - 8:00 AM PST' in html
