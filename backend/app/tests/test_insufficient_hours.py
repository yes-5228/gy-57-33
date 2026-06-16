from datetime import timedelta

import pytest

from app.models import Student
from app.store import next_id, students


class TestInsufficientHours:
    def test_exact_hours_sufficient(self, client, test_coach, future_slot):
        s = Student(id=next_id("student"), name="刚好够课时学员", phone="13800000100", remaining_hours=2, initial_hours=2)
        students[s.id] = s

        payload = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_hours_insufficient_rejected(self, client, test_student_low_hours, test_coach, future_slot):
        payload = {
            "student_id": test_student_low_hours.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 400
        assert "Student does not have enough remaining hours" in response.json()["detail"]

    def test_zero_hours_student_cannot_book(self, client, test_coach, future_slot):
        s = Student(id=next_id("student"), name="零课时学员", phone="13800000101", remaining_hours=0, initial_hours=0)
        students[s.id] = s

        payload = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=1)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 400

    def test_more_than_enough_hours(self, client, test_student, test_coach, future_slot):
        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=3)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_fractional_hours_insufficient(self, client, test_coach, future_slot):
        s = Student(id=next_id("student"), name="部分课时学员", phone="13800000102", remaining_hours=1, initial_hours=1)
        students[s.id] = s

        payload = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=1, minutes=30)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 400

    def test_fractional_hours_sufficient(self, client, test_coach, future_slot):
        s = Student(id=next_id("student"), name="足够部分课时学员", phone="13800000103", remaining_hours=2, initial_hours=2)
        students[s.id] = s

        payload = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=1, minutes=30)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_multiple_bookings_exhaust_hours(self, client, test_coach, future_slot):
        s = Student(id=next_id("student"), name="多段预约学员", phone="13800000104", remaining_hours=3, initial_hours=3)
        students[s.id] = s

        payload1 = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response1 = client.post("/api/appointments", json=payload1)
        assert response1.status_code == 201

        payload2 = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot + timedelta(hours=3)).isoformat(),
            "end_time": (future_slot + timedelta(hours=5)).isoformat(),
        }
        response2 = client.post("/api/appointments", json=payload2)
        assert response2.status_code == 400

    def test_booking_duration_calculation_precise(self, client, test_coach, future_slot):
        s = Student(id=next_id("student"), name="精确计算学员", phone="13800000105", remaining_hours=1, initial_hours=1)
        students[s.id] = s

        payload = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=1, minutes=6)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 400

    def test_exact_one_minute_less_than_available(self, client, test_coach, future_slot):
        s = Student(id=next_id("student"), name="边界学员", phone="13800000106", remaining_hours=1, initial_hours=1)
        students[s.id] = s

        payload = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(minutes=59)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201
