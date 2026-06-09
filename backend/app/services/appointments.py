from datetime import datetime

from fastapi import HTTPException, status

from app.models import Appointment, AppointmentStatus
from app.schemas import AppointmentCreate, AppointmentRead
from app.store import appointments, cancel_rule, coaches, next_id, students


def appointment_to_read(appointment: Appointment) -> AppointmentRead:
    student = students[appointment.student_id]
    coach = coaches[appointment.coach_id]
    return AppointmentRead(
        id=appointment.id,
        student_id=student.id,
        student_name=student.name,
        coach_id=coach.id,
        coach_name=coach.name,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        status=appointment.status,
        created_at=appointment.created_at,
        cancelled_at=appointment.cancelled_at,
        cancel_reason=appointment.cancel_reason,
    )


def list_appointments(status_filter: AppointmentStatus | None = None) -> list[AppointmentRead]:
    values = sorted(appointments.values(), key=lambda item: item.start_time)
    if status_filter:
        values = [item for item in values if item.status == status_filter]
    return [appointment_to_read(item) for item in values]


def create_appointment(payload: AppointmentCreate) -> AppointmentRead:
    if payload.student_id not in students:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    if payload.coach_id not in coaches or not coaches[payload.coach_id].active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Active coach not found")
    start_time = _as_naive(payload.start_time)
    end_time = _as_naive(payload.end_time)

    if start_time <= datetime.now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot book a past time slot")

    active_count = sum(
        1
        for item in appointments.values()
        if item.student_id == payload.student_id and item.status == AppointmentStatus.booked
    )
    if active_count >= cancel_rule.max_active_bookings_per_student:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Student has reached active booking limit")

    has_conflict = any(
        item.status == AppointmentStatus.booked
        and item.coach_id == payload.coach_id
        and start_time < item.end_time
        and end_time > item.start_time
        for item in appointments.values()
    )
    if has_conflict:
        raise HTTPException(status.HTTP_409_CONFLICT, "Coach already has a booking in this time slot")

    duration_hours = (end_time - start_time).total_seconds() / 3600
    if students[payload.student_id].remaining_hours < duration_hours:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Student does not have enough remaining hours")

    appointment = Appointment(
        id=next_id("appointment"),
        student_id=payload.student_id,
        coach_id=payload.coach_id,
        start_time=start_time,
        end_time=end_time,
        created_at=datetime.now(),
    )
    appointments[appointment.id] = appointment
    return appointment_to_read(appointment)


def _as_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone().replace(tzinfo=None)


def cancel_appointment(appointment_id: int, reason: str) -> AppointmentRead:
    appointment = appointments.get(appointment_id)
    if not appointment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Appointment already cancelled")
    if appointment.status == AppointmentStatus.completed and not cancel_rule.allow_cancel_completed:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Completed appointments cannot be cancelled")

    hours_before_start = (appointment.start_time - datetime.now()).total_seconds() / 3600
    if hours_before_start < cancel_rule.min_hours_before_start:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Appointments must be cancelled at least {cancel_rule.min_hours_before_start} hours in advance",
        )

    appointment.status = AppointmentStatus.cancelled
    appointment.cancelled_at = datetime.now()
    appointment.cancel_reason = reason
    appointments[appointment.id] = appointment
    return appointment_to_read(appointment)
