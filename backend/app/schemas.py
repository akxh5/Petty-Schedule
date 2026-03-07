from datetime import date
from typing import List, Optional, Any, Dict
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
    locations_per_day: int
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
    id: str
    created_at: date

    class Config:
        from_attributes = True

class Location(LocationBase):
    id: str
    created_at: date

    class Config:
        from_attributes = True

class DutySetting(DutySettingBase):
    id: str
    created_at: date

    class Config:
        from_attributes = True

class Constraint(ConstraintBase):
    id: str
    professor_id: str

    class Config:
        from_attributes = True

class RosterAssignment(RosterAssignmentBase):
    id: str

    class Config:
        from_attributes = True

class ProfessorWithDetails(Professor):
    constraints: List[Constraint] = []
    assignments: List[RosterAssignment] = []

    class Config:
        from_attributes = True
