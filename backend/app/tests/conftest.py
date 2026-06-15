from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Appointment, AppointmentStatus, CancelRule, Coach, Student
from app.store import appointments, cancel_rule, coaches, next_id, students


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    students.clear()
    coaches.clear()
    appointments.clear()
    cancel_rule.min_hours_before_start = 2
    cancel_rule.max_active_bookings_per_student = 3
    cancel_rule.allow_cancel_completed = False
    for key in next_id.__globals__["_ids"]:
        next_id.__globals__["_ids"][key] = 0


@pytest.fixture
def test_student():
    s = Student(id=next_id("student"), name="测试学员", phone="13800000001", remaining_hours=10)
    students[s.id] = s
    return s


@pytest.fixture
def test_student_low_hours():
    s = Student(id=next_id("student"), name="课时不足学员", phone="13800000002", remaining_hours=1)
    students[s.id] = s
    return s


@pytest.fixture
def test_coach():
    c = Coach(
        id=next_id("coach"),
        name="测试教练",
        phone="13900000001",
        car_no="粤B-TEST01",
        specialties=["科目二"],
        active=True,
    )
    coaches[c.id] = c
    return c


@pytest.fixture
def test_coach2():
    c = Coach(
        id=next_id("coach"),
        name="测试教练2",
        phone="13900000002",
        car_no="粤B-TEST02",
        specialties=["科目三"],
        active=True,
    )
    coaches[c.id] = c
    return c


@pytest.fixture
def inactive_coach():
    c = Coach(
        id=next_id("coach"),
        name="离职教练",
        phone="13900000003",
        car_no="粤B-TEST03",
        specialties=["科目二"],
        active=False,
    )
    coaches[c.id] = c
    return c


@pytest.fixture
def future_slot():
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    return now + timedelta(days=1, hours=10)


@pytest.fixture
def create_booking():
    def _create(student_id, coach_id, start_time, hours=2, status=AppointmentStatus.booked):
        end_time = start_time + timedelta(hours=hours)
        appt = Appointment(
            id=next_id("appointment"),
            student_id=student_id,
            coach_id=coach_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
            created_at=datetime.now(),
        )
        appointments[appt.id] = appt
        return appt

    return _create
