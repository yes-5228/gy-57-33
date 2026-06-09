from app.models import AppointmentStatus
from app.schemas import LessonStats
from app.store import appointments, students


def _hours(start, end) -> float:
    return round((end - start).total_seconds() / 3600, 1)


def lesson_stats() -> list[LessonStats]:
    result: list[LessonStats] = []
    for student in students.values():
        student_appointments = [item for item in appointments.values() if item.student_id == student.id]
        completed_hours = sum(
            _hours(item.start_time, item.end_time)
            for item in student_appointments
            if item.status == AppointmentStatus.completed
        )
        booked_hours = sum(
            _hours(item.start_time, item.end_time)
            for item in student_appointments
            if item.status == AppointmentStatus.booked
        )
        cancelled_count = sum(1 for item in student_appointments if item.status == AppointmentStatus.cancelled)
        result.append(
            LessonStats(
                student_id=student.id,
                student_name=student.name,
                completed_hours=round(completed_hours, 1),
                booked_hours=round(booked_hours, 1),
                cancelled_count=cancelled_count,
                remaining_hours=student.remaining_hours,
            )
        )
    return result
