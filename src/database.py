from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.motion_event import MotionEvent, Base
import datetime

class MotionEventDao:
    def __init__(self, db_url='sqlite:///motion_events.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add(self, event: MotionEvent):
        """Add a motion event to the database.
        
        Args:
            event (MotionEvent): The motion event to add.
        """
        session = self.Session()
        session.add(event)
        session.commit()
        session.close()

    def get(self, event_id):
        session = self.Session()
        event = session.query(MotionEvent).filter(MotionEvent.id == event_id).first()
        session.close()
        return event

    def list(self, start_time=None, end_time=None):
        session = self.Session()
        query = session.query(MotionEvent)
        if start_time is not None:
            query = query.filter(MotionEvent.start_timestamp >= start_time)
        if end_time is not None:
            query = query.filter(MotionEvent.start_timestamp <= end_time)
        events = query.all()
        session.close()
        return events