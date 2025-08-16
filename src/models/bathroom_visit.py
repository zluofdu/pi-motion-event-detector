from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class BathroomVisit(Base):
    __tablename__ = 'bathroom_visits'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String, nullable=False)
    visit_start = Column(DateTime, nullable=False)
    visit_end = Column(DateTime, nullable=False)
    event_count = Column(Integer, nullable=False)  # Number of motion events in this visit
    duration_seconds = Column(Integer, nullable=False)  # Visit duration
    detection_date = Column(DateTime, default=datetime.datetime.utcnow)  # When this visit was detected/aggregated
    
    def __repr__(self):
        return f"<BathroomVisit(id={self.id}, start={self.visit_start}, duration={self.duration_seconds}s, events={self.event_count})>"
