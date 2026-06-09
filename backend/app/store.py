from datetime import datetime, timedelta

from app.models import Appointment, AppointmentStatus, CancelRule, Coach, Student


students: dict[int, Student] = {}
coaches: dict[int, Coach] = {}
appointments: dict[int, Appointment] = {}
cancel_rule = CancelRule()

_ids = {"student": 0, "coach": 0, "appointment": 0}


def next_id(kind: str) -> int:
    _ids[kind] += 1
    return _ids[kind]


def seed_data() -> None:
    if students or coaches or appointments:
        return

    s1 = Student(id=next_id("student"), name="张小雨", phone="13800000001", remaining_hours=18)
    s2 = Student(id=next_id("student"), name="李明", phone="13800000002", remaining_hours=12)
    students[s1.id] = s1
    students[s2.id] = s2

    c1 = Coach(
        id=next_id("coach"),
        name="王教练",
        phone="13900000001",
        car_no="粤B-D1023",
        specialties=["科目二", "倒车入库"],
    )
    c2 = Coach(
        id=next_id("coach"),
        name="陈教练",
        phone="13900000002",
        car_no="粤B-D2048",
        specialties=["科目三", "道路驾驶"],
    )
    coaches[c1.id] = c1
    coaches[c2.id] = c2

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    appt = Appointment(
        id=next_id("appointment"),
        student_id=s1.id,
        coach_id=c1.id,
        start_time=now + timedelta(days=1, hours=1),
        end_time=now + timedelta(days=1, hours=3),
        status=AppointmentStatus.booked,
        created_at=now,
    )
    done = Appointment(
        id=next_id("appointment"),
        student_id=s2.id,
        coach_id=c2.id,
        start_time=now - timedelta(days=1, hours=3),
        end_time=now - timedelta(days=1, hours=1),
        status=AppointmentStatus.completed,
        created_at=now - timedelta(days=2),
    )
    appointments[appt.id] = appt
    appointments[done.id] = done
