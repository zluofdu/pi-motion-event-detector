import datetime
from typing import List, Tuple
from src.models.motion_event import MotionEvent
from src.models.bathroom_visit import BathroomVisit
from src.motion_event_dao import MotionEventDao
from src.timezone_utils import now_pst, to_pst, PST
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class BathroomVisitDetector:
    def __init__(self, db_url: str = 'sqlite:///motion_events.db', cluster_window_minutes: int = 5):
        """
        Initialize the bathroom visit detector.
        
        Args:
            db_url: Database connection string
            cluster_window_minutes: Time window to group motion events into visits
        """
        self.db_url = db_url
        self.cluster_window_minutes = cluster_window_minutes
        self.engine = create_engine(db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Ensure bathroom_visits table exists
        BathroomVisit.metadata.create_all(self.engine)
    
    def detect_visits_for_period(self, start_time: datetime.datetime, end_time: datetime.datetime) -> List[BathroomVisit]:
        """
        Detect bathroom visits from motion events in the given time period.
        
        Args:
            start_time: Start of detection period
            end_time: End of detection period
            
        Returns:
            List of detected bathroom visits
        """
        # Get motion events for the period
        dao = MotionEventDao(self.db_url)
        motion_events = dao.list(start_time, end_time)
        
        if len(motion_events) < 2:
            return []  # Need at least 2 events for a visit
        
        # Sort events by start time
        motion_events.sort(key=lambda e: e.start_timestamp)
        
        visits = []
        current_cluster = []
        
        for event in motion_events:
            if not current_cluster:
                # Start new cluster
                current_cluster = [event]
            else:
                # Check if this event is within the time window of the cluster
                cluster_start = current_cluster[0].start_timestamp
                time_diff = (event.start_timestamp - cluster_start).total_seconds() / 60
                
                if time_diff <= self.cluster_window_minutes:
                    # Add to current cluster
                    current_cluster.append(event)
                else:
                    # Process current cluster and start new one
                    if len(current_cluster) >= 2:
                        visit = self._create_visit_from_cluster(current_cluster)
                        visits.append(visit)
                    
                    current_cluster = [event]
        
        # Process the last cluster
        if len(current_cluster) >= 2:
            visit = self._create_visit_from_cluster(current_cluster)
            visits.append(visit)
        
        return visits
    
    def _create_visit_from_cluster(self, events: List[MotionEvent]) -> BathroomVisit:
        """Create a BathroomVisit from a cluster of motion events."""
        # Ensure timestamps are timezone-aware (convert to PST if needed)
        visit_start = events[0].start_timestamp
        visit_end = events[-1].stop_timestamp
        
        if visit_start.tzinfo is None:
            visit_start = PST.localize(visit_start)
        if visit_end.tzinfo is None:
            visit_end = PST.localize(visit_end)
            
        duration = (visit_end - visit_start).total_seconds()
        
        return BathroomVisit(
            device_id=events[0].device_id,
            visit_start=visit_start,
            visit_end=visit_end,
            event_count=len(events),
            duration_seconds=int(duration)
        )
    
    def save_visits(self, visits: List[BathroomVisit]) -> None:
        """Save detected visits to the database."""
        for visit in visits:
            self.session.add(visit)
        self.session.commit()
    
    def get_visits_for_date_range(self, start_date: datetime.date, end_date: datetime.date) -> List[BathroomVisit]:
        """Get all bathroom visits for a date range."""
        # Create timezone-aware datetimes in PST
        start_datetime = PST.localize(datetime.datetime.combine(start_date, datetime.time.min))
        end_datetime = PST.localize(datetime.datetime.combine(end_date, datetime.time.max))
        
        return self.session.query(BathroomVisit).filter(
            BathroomVisit.visit_start >= start_datetime,
            BathroomVisit.visit_start <= end_datetime
        ).order_by(BathroomVisit.visit_start).all()
    
    def close(self):
        """Close database session."""
        self.session.close()
