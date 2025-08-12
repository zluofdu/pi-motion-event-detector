from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
import datetime

Base = declarative_base()

class MotionEvent(Base):
    __tablename__ = 'motion_events'
    id = Column(Integer, primary_key=True)
    start_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    stop_timestamp = Column(DateTime)
    description = Column(String)
