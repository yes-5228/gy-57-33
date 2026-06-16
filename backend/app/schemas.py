from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.models import AppointmentStatus


class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=30)
    phone: str = Field(min_length=7, max_length=20)
    remaining_hours: float = Field(default=20, ge=0, le=200)


class StudentRead(StudentCreate):
    id: int


class CoachCreate(BaseModel):
    name: str = Field(min_length=2, max_length=30)
    phone: str = Field(min_length=7, max_length=20)
    car_no: str = Field(min_length=2, max_length=20)
    specialties: list[str] = Field(default_factory=list)
    active: bool = True


class CoachRead(CoachCreate):
    id: int


class AppointmentCreate(BaseModel):
    student_id: int
    coach_id: int
    start_time: datetime
    end_time: datetime

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, value: datetime, info):
        start_time = info.data.get("start_time")
        if start_time and value <= start_time:
            raise ValueError("end_time must be later than start_time")
        return value


class AppointmentRead(BaseModel):
    id: int
    student_id: int
    student_name: str
    coach_id: int
    coach_name: str
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    created_at: datetime
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None


class AppointmentCancel(BaseModel):
    reason: str = Field(default="学员主动取消", min_length=2, max_length=100)


class LessonStats(BaseModel):
    student_id: int
    student_name: str
    completed_hours: float
    booked_hours: float
    cancelled_count: int
    remaining_hours: float


class DashboardSummary(BaseModel):
    total_students: int
    total_coaches: int
    active_bookings: int
    completed_hours: float
    cancel_rule: dict[str, int | bool]
