from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Interval, Time
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta, timezone

Base = declarative_base()



class Post(Base):
  __tablename__ = "post"
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  title = Column(String(255), nullable=False)
  content = Column(Text, nullable=False)
  media_content = Column(Text, nullable=True)
  schedule_time = Column(Time, nullable=True)
  is_active = Column(Boolean, default=True)
  repeat_interval = Column(Interval, default=timedelta(days=1))
  created_at = Column(
    DateTime, 
    default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
  )
  updated_at = Column(
    DateTime, 
    default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
  )
  

class User(Base):
  __tablename__ = "user"
  
  id = Column(Integer, primary_key=True, autoincrement=True)
  tg_id = Column(Integer, unique=True, nullable=False)
  username = Column(String(255), nullable=True)
  created_at = Column(
    DateTime,
    default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
  )