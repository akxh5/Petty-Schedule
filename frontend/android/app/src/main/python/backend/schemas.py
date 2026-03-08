from datetime import date, datetime
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel
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
    professor_id: UUID
    location_id: UUID
    date: date

# Create Schemas
class ProfessorCreate(ProfessorBase):
    pass

class LocationCreate(LocationBase):
    pass

class DutySettingCreate(DutySettingBase):
    pass

class ConstraintCreate(ConstraintBase):
    professor_id: UUID

# Response Schemas
class Professor(ProfessorBase):
    id: UUID
    created_at: date
    class Config:
        orm_mode = True

class Location(LocationBase):
    id: UUID
    created_at: date
    class Config:
        orm_mode = True

class DutySetting(DutySettingBase):
    id: UUID
    created_at: datetime
    class Config:
        orm_mode = True

class Constraint(ConstraintBase):
    id: UUID
    professor_id: UUID
    class Config:
        orm_mode = True

class RosterAssignment(RosterAssignmentBase):
    id: UUID
    class Config:
        orm_mode = True

class ProfessorWithDetails(Professor):
    constraints: List[Constraint] = []
    assignments: List[RosterAssignment] = []
    class Config:
        orm_mode = True
