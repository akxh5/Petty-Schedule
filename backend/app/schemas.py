from datetime import date, datetime
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from .models import ConstraintType

# Base Schemas
class ProfessorBase(BaseModel):
    name: str
    code: str

class LocationBase(BaseModel):
    name: str

class DutySettingBase(BaseModel):
    start_date: date
    end_date: date
    count_sundays: bool = True

class ConstraintBase(BaseModel):
    type: ConstraintType
    value: Dict[str, Any]

class RosterAssignmentBase(BaseModel):
    professor_id: str
    location_id: str
    date: date

# Create Schemas
class ProfessorCreate(ProfessorBase):
    pass

class LocationCreate(LocationBase):
    pass

class DutySettingCreate(DutySettingBase):
    pass

class ConstraintCreate(ConstraintBase):
    professor_id: str

# Response Schemas
class Professor(ProfessorBase):
    id: UUID
    created_at: date
    model_config = ConfigDict(from_attributes=True)

class Location(LocationBase):
    id: UUID
    created_at: date
    model_config = ConfigDict(from_attributes=True)

class DutySetting(DutySettingBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Constraint(ConstraintBase):
    id: UUID
    professor_id: str
    model_config = ConfigDict(from_attributes=True)

class RosterAssignment(RosterAssignmentBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class ProfessorWithDetails(Professor):
    constraints: List[Constraint] = []
    assignments: List[RosterAssignment] = []
    model_config = ConfigDict(from_attributes=True)
