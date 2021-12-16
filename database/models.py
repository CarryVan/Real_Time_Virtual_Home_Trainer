from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relation, relationship
from sqlalchemy.sql.sqltypes import DATETIME

from database import Base
from datetime import datetime

class WorkoutFlow(Base):

    __tablename__ = "workout_flow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workout_session = Column(Integer, ForeignKey("workout_session.id"))
    workout_name  = Column(String, index=True)
    sequence = Column(Integer, index=True)
    set = Column(Integer, index=True)
    count = Column(Integer, index=True)
    breaktime = Column(Integer, index=True)

    # workout_session = relationship("workout_count", back_populates="workout_done_check")

class WorkoutSession(Base):

    __tablename__ = "workout_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_time = Column(DATETIME, default=datetime.utcnow)

    # workout_flow = relationship("workout_count", back_populates="workout_done_check")

# class User(Base):

#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True)
#     hashed_password = Column(String)
#     is_active = Column(Boolean, default=True)

#     items = relationship("Item", back_populates="owner")

# class Item(Base):

#     __tablename__ = "items"

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, index=True)
#     description = Column(String, index=True)
#     owner_id = Column(Integer, ForeignKey("users.id"))

#     owner = relationship("User", back_populates="items")