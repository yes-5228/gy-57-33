from fastapi import APIRouter

from app.models import AppointmentStatus
from app.schemas import DashboardSummary, LessonStats
from app.services.stats import lesson_stats
from app.store import appointments, cancel_rule, coaches, students

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def summary() -> DashboardSummary:
    completed_hours = sum(
        (item.end_time - item.start_time).total_seconds() / 3600
        for item in appointments.values()
        if item.status == AppointmentStatus.completed
    )
    return DashboardSummary(
        total_students=len(students),
        total_coaches=len(coaches),
        active_bookings=sum(1 for item in appointments.values() if item.status == AppointmentStatus.booked),
        completed_hours=round(completed_hours, 1),
        cancel_rule=cancel_rule.model_dump(),
    )


@router.get("/lesson-stats", response_model=list[LessonStats])
def get_lesson_stats() -> list[LessonStats]:
    return lesson_stats()
