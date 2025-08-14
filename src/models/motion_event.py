from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class MotionEvent(Base):
    __tablename__ = 'motion_events'
    id = Column(Integer, primary_key=True)
    device_id = Column(String, nullable=False)  # Identifier for the motion detector device
    start_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    stop_timestamp = Column(DateTime)
