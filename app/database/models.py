from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Interval
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta, timezone

Base = declarative_base()



class Post(Base):
  __tablename__ = "post"
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  title = Column(String(255), nullable=False)
  content = Column(Text, nullable=False)
  media_content = Column(Text, nullable=True)
  schedule_time = Column(DateTime, nullable=True)
  is_active = Column(Boolean, default=True)
  repeat_interval = Column(Interval, default=timedelta(days=1))
  created_at = Column(DateTime, default=datetime.now(timezone.utc))
  updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))