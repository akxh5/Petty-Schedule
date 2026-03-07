import uuid
import datetime
import enum
from sqlalchemy import Column, String, Date, Integer, ForeignKey, Enum, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ConstraintType(str, enum.Enum):
    DAY_UNAVAILABLE = "DAY_UNAVAILABLE"
    DAY_PREFERRED = "DAY_PREFERRED"
    LOCATION_RESTRICTED = "LOCATION_RESTRICTED"
    MAX_WEEKLY = "MAX_WEEKLY"

class Professor(Base):
    __tablename__ = "professors"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    created_at = Column(Date, default=datetime.date.today)

    constraints = relationship("Constraint", back_populates="professor", cascade="all, delete-orphan")
    assignments = relationship("RosterAssignment", back_populates="professor", cascade="all, delete-orphan")

class Location(Base):
    __tablename__ = "locations"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(Date, default=datetime.date.today)

    assignments = relationship("RosterAssignment", back_populates="location", cascade="all, delete-orphan")

class DutySetting(Base):
    __tablename__ = "duty_settings"

    id = Column(String, primary_key=True, default=generate_uuid)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    locations_per_day = Column(Integer, default=3)
    count_sundays = Column(Integer, default=1) # Boolean equivalent for sqlite/postgres compatibility
    created_at = Column(Date, default=datetime.date.today)

class Constraint(Base):
    __tablename__ = "constraints"

    id = Column(String, primary_key=True, default=generate_uuid)
    professor_id = Column(String, ForeignKey("professors.id"), nullable=False)
    type = Column(Enum(ConstraintType), nullable=False)
    value = Column(JSON, nullable=False)

    professor = relationship("Professor", back_populates="constraints")

class RosterAssignment(Base):
    __tablename__ = "roster_assignments"

    id = Column(String, primary_key=True, default=generate_uuid)
    professor_id = Column(String, ForeignKey("professors.id"), nullable=False)
    location_id = Column(String, ForeignKey("locations.id"), nullable=False)
    date = Column(Date, nullable=False)

    professor = relationship("Professor", back_populates="assignments")
    location = relationship("Location", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint('professor_id', 'date', name='uq_professor_date'),
    )
