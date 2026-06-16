from datetime import timedelta

import pytest

from app.models import AppointmentStatus, Student
from app.store import next_id, students


class TestAppointmentConflict:
    def test_full_overlap_conflict(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 409
        assert "Coach already has a booking in this time slot" in response.json()["detail"]

    def test_partial_overlap_start_conflict(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot - timedelta(hours=1)).isoformat(),
            "end_time": (future_slot + timedelta(hours=1)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 409

    def test_partial_overlap_end_conflict(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot + timedelta(hours=1)).isoformat(),
            "end_time": (future_slot + timedelta(hours=3)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 409

    def test_contained_within_conflict(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, hours=3)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot + timedelta(minutes=30)).isoformat(),
            "end_time": (future_slot + timedelta(hours=1, minutes=30)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 409

    def test_contains_existing_conflict(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, hours=1)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot - timedelta(hours=1)).isoformat(),
            "end_time": (future_slot + timedelta(hours=3)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 409

    def test_no_conflict_adjacent_before(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot - timedelta(hours=2)).isoformat(),
            "end_time": future_slot.isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_no_conflict_adjacent_after(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot + timedelta(hours=2)).isoformat(),
            "end_time": (future_slot + timedelta(hours=4)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_no_conflict_different_coach(self, client, test_coach, test_coach2, future_slot, create_booking):
        s1 = Student(id=next_id("student"), name="学员1", phone="13800000901", remaining_hours=10)
        s2 = Student(id=next_id("student"), name="学员2", phone="13800000902", remaining_hours=10)
        students[s1.id] = s1
        students[s2.id] = s2

        create_booking(s1.id, test_coach.id, future_slot)

        payload = {
            "student_id": s2.id,
            "coach_id": test_coach2.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_no_conflict_cancelled_appointment(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, status=AppointmentStatus.cancelled)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_no_conflict_completed_appointment(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, status=AppointmentStatus.completed)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_multiple_consecutive_bookings_no_conflict(self, client, test_student, test_coach, future_slot):
        for i in range(3):
            start = future_slot + timedelta(hours=i * 2)
            payload = {
                "student_id": test_student.id,
                "coach_id": test_coach.id,
                "start_time": start.isoformat(),
                "end_time": (start + timedelta(hours=2)).isoformat(),
            }
            response = client.post("/api/appointments", json=payload)
            assert response.status_code == 201

    def test_conflict_within_gap_between_bookings(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot)
        create_booking(test_student.id, test_coach.id, future_slot + timedelta(hours=4))

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot + timedelta(hours=1, minutes=30)).isoformat(),
            "end_time": (future_slot + timedelta(hours=3, minutes=30)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 409
