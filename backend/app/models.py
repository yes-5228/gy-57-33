from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AppointmentStatus(str, Enum):
    booked = "booked"
    cancelled = "cancelled"
    completed = "completed"


class Student(BaseModel):
    id: int
    name: str
    phone: str
    remaining_hours: int = Field(ge=0)


class Coach(BaseModel):
    id: int
    name: str
    phone: str
    car_no: str
    specialties: list[str]
    active: bool = True


class Appointment(BaseModel):
    id: int
    student_id: int
    coach_id: int
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus = AppointmentStatus.booked
    created_at: datetime
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None


class CancelRule(BaseModel):
    min_hours_before_start: int = 2
    max_active_bookings_per_student: int = 3
    allow_cancel_completed: bool = False
