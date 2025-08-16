import pytest
import datetime
from src.models.bathroom_visit import BathroomVisit
from src.timezone_utils import pst_from_naive
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestBathroomVisitModel:
    """Test suite for the BathroomVisit SQLAlchemy model."""

    @pytest.fixture
    def engine(self):
        """Create in-memory SQLite engine for testing."""
        engine = create_engine('sqlite:///:memory:')
        BathroomVisit.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def session(self, engine):
        """Create database session for testing."""
        Session = sessionmaker(bind=engine)
        return Session()

    @pytest.fixture
    def sample_visit(self):
        """Create a sample bathroom visit for testing."""
        start_time = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 30, 0))
        end_time = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 35, 30))
        
        return BathroomVisit(
            device_id='pir_sensor_4',
            visit_start=start_time,
            visit_end=end_time,
            event_count=3,
            duration_seconds=330
        )

    def test_bathroom_visit_creation(self, sample_visit):
        """Test creating a bathroom visit instance."""
        assert sample_visit.device_id == 'pir_sensor_4'
        assert sample_visit.event_count == 3
        assert sample_visit.duration_seconds == 330
        
        # Check timestamps
        assert sample_visit.visit_start.hour == 2
        assert sample_visit.visit_start.minute == 30
        assert sample_visit.visit_end.hour == 2
        assert sample_visit.visit_end.minute == 35
        assert sample_visit.visit_end.second == 30

    def test_bathroom_visit_timezone_aware(self, sample_visit):
        """Test that bathroom visit handles timezone-aware timestamps."""
        assert sample_visit.visit_start.tzinfo is not None
        assert sample_visit.visit_end.tzinfo is not None
        assert sample_visit.visit_start.tzinfo.zone == 'US/Pacific'
        assert sample_visit.visit_end.tzinfo.zone == 'US/Pacific'

    def test_bathroom_visit_database_operations(self, session, sample_visit):
        """Test database CRUD operations."""
        # Create
        session.add(sample_visit)
        session.commit()
        
        # Read
        retrieved_visit = session.query(BathroomVisit).filter_by(device_id='pir_sensor_4').first()
        
        assert retrieved_visit is not None
        assert retrieved_visit.device_id == 'pir_sensor_4'
        assert retrieved_visit.event_count == 3
        assert retrieved_visit.duration_seconds == 330
        
        # Update
        retrieved_visit.event_count = 4
        session.commit()
        
        updated_visit = session.query(BathroomVisit).filter_by(device_id='pir_sensor_4').first()
        assert updated_visit.event_count == 4
        
        # Delete
        session.delete(updated_visit)
        session.commit()
        
        deleted_visit = session.query(BathroomVisit).filter_by(device_id='pir_sensor_4').first()
        assert deleted_visit is None

    def test_bathroom_visit_multiple_records(self, session):
        """Test storing multiple bathroom visits."""
        visits = []
        base_time = datetime.datetime(2025, 8, 14, 1, 0, 0)
        
        # Create 5 visits
        for i in range(5):
            start_time = pst_from_naive(base_time + datetime.timedelta(hours=i))
            end_time = start_time + datetime.timedelta(minutes=5)
            
            visit = BathroomVisit(
                device_id=f'pir_sensor_{i}',
                visit_start=start_time,
                visit_end=end_time,
                event_count=2 + i,
                duration_seconds=300 + i*60
            )
            visits.append(visit)
            session.add(visit)
        
        session.commit()
        
        # Query all visits
        all_visits = session.query(BathroomVisit).all()
        assert len(all_visits) == 5
        
        # Query visits by device
        device_0_visits = session.query(BathroomVisit).filter_by(device_id='pir_sensor_0').all()
        assert len(device_0_visits) == 1
        assert device_0_visits[0].event_count == 2

    def test_bathroom_visit_time_range_query(self, session):
        """Test querying visits within time ranges."""
        # Create visits at different times
        times = [
            datetime.datetime(2025, 8, 14, 1, 0, 0),   # 1 AM
            datetime.datetime(2025, 8, 14, 3, 0, 0),   # 3 AM  
            datetime.datetime(2025, 8, 14, 5, 0, 0),   # 5 AM
            datetime.datetime(2025, 8, 14, 7, 0, 0),   # 7 AM
        ]
        
        for i, time in enumerate(times):
            start_time = pst_from_naive(time)
            end_time = start_time + datetime.timedelta(minutes=5)
            
            visit = BathroomVisit(
                device_id='pir_sensor_4',
                visit_start=start_time,
                visit_end=end_time,
                event_count=2,
                duration_seconds=300
            )
            session.add(visit)
        
        session.commit()
        
        # Query visits between 2 AM and 6 AM
        start_range = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 0, 0))
        end_range = pst_from_naive(datetime.datetime(2025, 8, 14, 6, 0, 0))
        
        visits_in_range = session.query(BathroomVisit).filter(
            BathroomVisit.visit_start >= start_range,
            BathroomVisit.visit_start <= end_range
        ).all()
        
        assert len(visits_in_range) == 2  # 3 AM and 5 AM visits
        assert visits_in_range[0].visit_start.hour == 3
        assert visits_in_range[1].visit_start.hour == 5

    def test_bathroom_visit_ordering(self, session):
        """Test ordering visits by timestamp."""
        # Create visits in reverse chronological order
        times = [
            datetime.datetime(2025, 8, 14, 7, 0, 0),   # Latest
            datetime.datetime(2025, 8, 14, 3, 0, 0),   # Middle
            datetime.datetime(2025, 8, 14, 1, 0, 0),   # Earliest
        ]
        
        for i, time in enumerate(times):
            start_time = pst_from_naive(time)
            end_time = start_time + datetime.timedelta(minutes=5)
            
            visit = BathroomVisit(
                device_id='pir_sensor_4',
                visit_start=start_time,
                visit_end=end_time,
                event_count=i+1,  # Use as identifier
                duration_seconds=300
            )
            session.add(visit)
        
        session.commit()
        
        # Query with ordering
        ordered_visits = session.query(BathroomVisit).order_by(BathroomVisit.visit_start).all()
        
        assert len(ordered_visits) == 3
        assert ordered_visits[0].visit_start.hour == 1  # Earliest first
        assert ordered_visits[1].visit_start.hour == 3
        assert ordered_visits[2].visit_start.hour == 7  # Latest last

    def test_bathroom_visit_duration_calculation(self):
        """Test duration calculations for visits."""
        start_time = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 30, 0))
        end_time = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 35, 45))
        
        visit = BathroomVisit(
            device_id='pir_sensor_4',
            visit_start=start_time,
            visit_end=end_time,
            event_count=2,
            duration_seconds=345  # 5 minutes 45 seconds
        )
        
        # Verify calculated duration matches stored duration
        calculated_duration = (end_time - start_time).total_seconds()
        assert visit.duration_seconds == int(calculated_duration)
        assert visit.duration_seconds == 345

    def test_bathroom_visit_with_naive_timestamps(self, session):
        """Test that model handles naive timestamps properly."""
        # Create visit with naive timestamps (simulating old data)
        start_time = datetime.datetime(2025, 8, 14, 2, 30, 0)  # Naive
        end_time = datetime.datetime(2025, 8, 14, 2, 35, 0)    # Naive
        
        visit = BathroomVisit(
            device_id='pir_sensor_4',
            visit_start=start_time,
            visit_end=end_time,
            event_count=2,
            duration_seconds=300
        )
        
        session.add(visit)
        session.commit()
        
        # Retrieve and verify
        retrieved_visit = session.query(BathroomVisit).first()
        assert retrieved_visit.visit_start == start_time
        assert retrieved_visit.visit_end == end_time

    def test_bathroom_visit_string_representation(self, sample_visit):
        """Test string representation of bathroom visit."""
        str_repr = str(sample_visit)
        
        # Should contain key information
        assert 'BathroomVisit' in str_repr
        assert 'start=' in str_repr
        assert 'duration=' in str_repr
        assert 'events=' in str_repr

    def test_bathroom_visit_edge_cases(self, session):
        """Test edge cases for bathroom visits."""
        # Very short visit (1 second)
        start_time = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 30, 0))
        end_time = pst_from_naive(datetime.datetime(2025, 8, 14, 2, 30, 1))
        
        short_visit = BathroomVisit(
            device_id='pir_sensor_4',
            visit_start=start_time,
            visit_end=end_time,
            event_count=2,
            duration_seconds=1
        )
        
        session.add(short_visit)
        
        # Very long visit (30 minutes)
        start_time_long = pst_from_naive(datetime.datetime(2025, 8, 14, 3, 0, 0))
        end_time_long = pst_from_naive(datetime.datetime(2025, 8, 14, 3, 30, 0))
        
        long_visit = BathroomVisit(
            device_id='pir_sensor_4',
            visit_start=start_time_long,
            visit_end=end_time_long,
            event_count=10,
            duration_seconds=1800
        )
        
        session.add(long_visit)
        session.commit()
        
        # Verify both stored correctly
        visits = session.query(BathroomVisit).order_by(BathroomVisit.duration_seconds).all()
        assert len(visits) == 2
        assert visits[0].duration_seconds == 1
        assert visits[1].duration_seconds == 1800

    def test_bathroom_visit_same_device_multiple_visits(self, session):
        """Test multiple visits from same device."""
        device_id = 'pir_sensor_4'
        
        # Create 3 visits for same device
        for i in range(3):
            start_time = pst_from_naive(datetime.datetime(2025, 8, 14, i+1, 0, 0))
            end_time = start_time + datetime.timedelta(minutes=5)
            
            visit = BathroomVisit(
                device_id=device_id,
                visit_start=start_time,
                visit_end=end_time,
                event_count=2,
                duration_seconds=300
            )
            session.add(visit)
        
        session.commit()
        
        # Query visits for specific device
        device_visits = session.query(BathroomVisit).filter_by(device_id=device_id).all()
        assert len(device_visits) == 3
        
        # All should have same device_id
        for visit in device_visits:
            assert visit.device_id == device_id
