import pytest
import datetime
from unittest.mock import Mock, patch, MagicMock
from src.bathroom_visit_detector import BathroomVisitDetector
from src.models.motion_event import MotionEvent
from src.models.bathroom_visit import BathroomVisit
from src.timezone_utils import PST, pst_from_naive

class TestBathroomVisitDetector:
    """Test suite for bathroom visit detection logic."""

    @pytest.fixture
    def mock_dao(self):
        """Mock motion event DAO."""
        dao = Mock()
        return dao

    @pytest.fixture
    def detector(self, mock_dao):
        """Create detector with mocked dependencies."""
        with patch('src.bathroom_visit_detector.MotionEventDao') as mock_dao_class:
            mock_dao_class.return_value = mock_dao
            with patch('src.bathroom_visit_detector.create_engine') as mock_engine:
                with patch('src.bathroom_visit_detector.sessionmaker') as mock_session_maker:
                    mock_session = Mock()
                    mock_session_maker.return_value = mock_session
                    
                    detector = BathroomVisitDetector(db_url='sqlite:///:memory:')
                    detector.session = mock_session
                    return detector

    def create_motion_event(self, device_id, start_time, duration_seconds=60):
        """Helper to create motion events for testing."""
        start_timestamp = pst_from_naive(start_time)
        stop_timestamp = start_timestamp + datetime.timedelta(seconds=duration_seconds)
        
        return MotionEvent(
            device_id=device_id,
            start_timestamp=start_timestamp,
            stop_timestamp=stop_timestamp
        )

    def test_initialization(self, detector):
        """Test detector initialization."""
        assert detector.cluster_window_minutes == 5
        assert detector.db_url == 'sqlite:///:memory:'

    def test_initialization_custom_window(self):
        """Test detector with custom clustering window."""
        with patch('src.bathroom_visit_detector.create_engine'):
            with patch('src.bathroom_visit_detector.sessionmaker'):
                detector = BathroomVisitDetector(cluster_window_minutes=10)
                assert detector.cluster_window_minutes == 10

    def test_detect_visits_no_events(self, detector):
        """Test detection with no motion events."""
        with patch.object(detector, 'session'):
            with patch('src.bathroom_visit_detector.MotionEventDao') as mock_dao_class:
                mock_dao = Mock()
                mock_dao.list.return_value = []
                mock_dao_class.return_value = mock_dao
                
                start_time = datetime.datetime(2025, 8, 14, 0, 30)
                end_time = datetime.datetime(2025, 8, 14, 8, 0)
                
                visits = detector.detect_visits_for_period(start_time, end_time)
                assert visits == []

    def test_detect_visits_insufficient_events(self, detector):
        """Test detection with only one motion event."""
        with patch.object(detector, 'session'):
            with patch('src.bathroom_visit_detector.MotionEventDao') as mock_dao_class:
                mock_dao = Mock()
                
                # Only one event - insufficient for visit
                events = [
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 0))
                ]
                mock_dao.list.return_value = events
                mock_dao_class.return_value = mock_dao
                
                start_time = datetime.datetime(2025, 8, 14, 0, 30)
                end_time = datetime.datetime(2025, 8, 14, 8, 0)
                
                visits = detector.detect_visits_for_period(start_time, end_time)
                assert visits == []

    def test_detect_visits_single_cluster(self, detector):
        """Test detection with events forming single visit."""
        with patch.object(detector, 'session'):
            with patch('src.bathroom_visit_detector.MotionEventDao') as mock_dao_class:
                mock_dao = Mock()
                
                # Two events within 5 minutes - should form one visit
                events = [
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 0)),
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 3))
                ]
                mock_dao.list.return_value = events
                mock_dao_class.return_value = mock_dao
                
                start_time = datetime.datetime(2025, 8, 14, 0, 30)
                end_time = datetime.datetime(2025, 8, 14, 8, 0)
                
                visits = detector.detect_visits_for_period(start_time, end_time)
                
                assert len(visits) == 1
                visit = visits[0]
                assert visit.device_id == 'pir_sensor_4'
                assert visit.event_count == 2
                assert visit.duration_seconds == 240  # 4 minutes total (2:00-2:04)

    def test_detect_visits_multiple_clusters(self, detector):
        """Test detection with events forming multiple visits."""
        with patch.object(detector, 'session'):
            with patch('src.bathroom_visit_detector.MotionEventDao') as mock_dao_class:
                mock_dao = Mock()
                
                # Events forming two separate visits
                events = [
                    # First visit: 2:00-2:03
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 0)),
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 2)),
                    
                    # Second visit: 2:10-2:12 (7 minutes later - separate visit)
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 10)),
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 11))
                ]
                mock_dao.list.return_value = events
                mock_dao_class.return_value = mock_dao
                
                start_time = datetime.datetime(2025, 8, 14, 0, 30)
                end_time = datetime.datetime(2025, 8, 14, 8, 0)
                
                visits = detector.detect_visits_for_period(start_time, end_time)
                
                assert len(visits) == 2
                
                # First visit
                assert visits[0].event_count == 2
                assert visits[0].visit_start.hour == 2
                assert visits[0].visit_start.minute == 0
                
                # Second visit  
                assert visits[1].event_count == 2
                assert visits[1].visit_start.hour == 2
                assert visits[1].visit_start.minute == 10

    def test_detect_visits_cluster_boundary(self, detector):
        """Test events exactly at cluster window boundary."""
        with patch.object(detector, 'session'):
            with patch('src.bathroom_visit_detector.MotionEventDao') as mock_dao_class:
                mock_dao = Mock()
                
                # Events exactly 5 minutes apart - should be in same cluster
                events = [
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 0)),
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 5))  # Exactly 5 min
                ]
                mock_dao.list.return_value = events
                mock_dao_class.return_value = mock_dao
                
                start_time = datetime.datetime(2025, 8, 14, 0, 30)
                end_time = datetime.datetime(2025, 8, 14, 8, 0)
                
                visits = detector.detect_visits_for_period(start_time, end_time)
                
                assert len(visits) == 1  # Should form one visit

    def test_detect_visits_over_cluster_boundary(self, detector):
        """Test events just over cluster window boundary."""
        with patch.object(detector, 'session'):
            with patch('src.bathroom_visit_detector.MotionEventDao') as mock_dao_class:
                mock_dao = Mock()
                
                # Events just over 5 minutes apart - should be separate visits
                events = [
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 0)),
                    self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 5, 30))  # 5:30 apart
                ]
                mock_dao.list.return_value = events
                mock_dao_class.return_value = mock_dao
                
                start_time = datetime.datetime(2025, 8, 14, 0, 30)
                end_time = datetime.datetime(2025, 8, 14, 8, 0)
                
                visits = detector.detect_visits_for_period(start_time, end_time)
                
                assert len(visits) == 0  # Each event alone - insufficient for visits

    def test_create_visit_from_cluster(self, detector):
        """Test creating bathroom visit from event cluster."""
        events = [
            self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 0), 60),
            self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 2), 30),
            self.create_motion_event('pir_sensor_4', datetime.datetime(2025, 8, 14, 2, 4), 45)
        ]
        
        visit = detector._create_visit_from_cluster(events)
        
        assert visit.device_id == 'pir_sensor_4'
        assert visit.event_count == 3
        assert visit.visit_start == events[0].start_timestamp
        assert visit.visit_end == events[-1].stop_timestamp
        
        # Duration from first start to last stop: 2:00:00 to 2:04:45 = 4:45 = 285 seconds
        expected_duration = (
            events[-1].stop_timestamp - events[0].start_timestamp
        ).total_seconds()
        assert visit.duration_seconds == int(expected_duration)

    def test_create_visit_timezone_handling(self, detector):
        """Test that visit creation handles timezone-aware timestamps."""
        # Create events with naive timestamps (simulating database retrieval)
        events = [
            MotionEvent(
                device_id='pir_sensor_4',
                start_timestamp=datetime.datetime(2025, 8, 14, 2, 0),  # Naive
                stop_timestamp=datetime.datetime(2025, 8, 14, 2, 1)
            ),
            MotionEvent(
                device_id='pir_sensor_4', 
                start_timestamp=datetime.datetime(2025, 8, 14, 2, 2),  # Naive
                stop_timestamp=datetime.datetime(2025, 8, 14, 2, 3)
            )
        ]
        
        visit = detector._create_visit_from_cluster(events)
        
        # Should convert to PST timezone
        assert visit.visit_start.tzinfo.zone == 'US/Pacific'
        assert visit.visit_end.tzinfo.zone == 'US/Pacific'

    def test_save_visits(self, detector):
        """Test saving visits to database."""
        visits = [
            BathroomVisit(
                device_id='pir_sensor_4',
                visit_start=pst_from_naive(datetime.datetime(2025, 8, 14, 2, 0)),
                visit_end=pst_from_naive(datetime.datetime(2025, 8, 14, 2, 5)),
                event_count=2,
                duration_seconds=300
            )
        ]
        
        detector.save_visits(visits)
        
        # Check that session.add was called for each visit
        assert detector.session.add.call_count == 1
        detector.session.commit.assert_called_once()

    def test_get_visits_for_date_range(self, detector):
        """Test retrieving visits for date range."""
        start_date = datetime.date(2025, 8, 14)
        end_date = datetime.date(2025, 8, 15)
        
        # Mock query chain
        mock_query = Mock()
        mock_filtered = Mock()
        mock_ordered = Mock()
        
        detector.session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filtered
        mock_filtered.order_by.return_value = mock_ordered
        mock_ordered.all.return_value = []
        
        result = detector.get_visits_for_date_range(start_date, end_date)
        
        # Verify query was constructed correctly
        detector.session.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_filtered.order_by.assert_called_once()
        mock_ordered.all.assert_called_once()
        
        assert result == []

    def test_close(self, detector):
        """Test closing database session."""
        detector.close()
        detector.session.close.assert_called_once()

    def test_large_cluster_handling(self, detector):
        """Test handling of large event clusters."""
        with patch.object(detector, 'session'):
            with patch('src.bathroom_visit_detector.MotionEventDao') as mock_dao_class:
                mock_dao = Mock()
                
                # Create 10 events within 5 minutes
                events = []
                for i in range(10):
                    events.append(
                        self.create_motion_event(
                            'pir_sensor_4', 
                            datetime.datetime(2025, 8, 14, 2, 0) + datetime.timedelta(seconds=i*20),
                            10
                        )
                    )
                
                mock_dao.list.return_value = events
                mock_dao_class.return_value = mock_dao
                
                start_time = datetime.datetime(2025, 8, 14, 0, 30)
                end_time = datetime.datetime(2025, 8, 14, 8, 0)
                
                visits = detector.detect_visits_for_period(start_time, end_time)
                
                assert len(visits) == 1
                assert visits[0].event_count == 10
