import uuid
import datetime
import enum
from sqlalchemy import Column, String, Date, Integer, ForeignKey, Enum, JSON, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class ConstraintType(str, enum.Enum):
    DAY_UNAVAILABLE = "DAY_UNAVAILABLE"
    DAY_PREFERRED = "DAY_PREFERRED"
    LOCATION_RESTRICTED = "LOCATION_RESTRICTED"
    MAX_WEEKLY = "MAX_WEEKLY"

class Professor(Base):
    __tablename__ = "professors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    created_at = Column(Date, default=datetime.date.today)

    constraints = relationship("Constraint", back_populates="professor", cascade="all, delete-orphan")
    assignments = relationship("RosterAssignment", back_populates="professor", cascade="all, delete-orphan")

class Location(Base):
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(Date, default=datetime.date.today)

    assignments = relationship("RosterAssignment", back_populates="location", cascade="all, delete-orphan")

class DutySetting(Base):
    __tablename__ = "duty_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    count_sundays = Column(Integer, default=1) # Boolean equivalent for sqlite/postgres compatibility
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Constraint(Base):
    __tablename__ = "constraints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("professors.id"), nullable=False)
    type = Column(Enum(ConstraintType), nullable=False)
    value = Column(JSON, nullable=False)

    professor = relationship("Professor", back_populates="constraints")

class RosterAssignment(Base):
    __tablename__ = "roster_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("professors.id"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    date = Column(Date, nullable=False)

    professor = relationship("Professor", back_populates="assignments")
    location = relationship("Location", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint('professor_id', 'date', name='uq_professor_date'),
    )
