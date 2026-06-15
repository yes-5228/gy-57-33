from datetime import datetime, timedelta

import pytest

from app.models import AppointmentStatus, Student
from app.store import cancel_rule, next_id, students


class TestBookingFlowWithRuleChanges:
    def test_full_booking_flow_before_and_after_rule_change(self, client, test_coach):
        s1 = Student(id=next_id("student"), name="流程测试学员", phone="13800000401", remaining_hours=20)
        students[s1.id] = s1

        future1 = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1, hours=10)
        future2 = future1 + timedelta(hours=3)
        future3 = future1 + timedelta(days=1)

        payload1 = {
            "student_id": s1.id,
            "coach_id": test_coach.id,
            "start_time": future1.isoformat(),
            "end_time": (future1 + timedelta(hours=2)).isoformat(),
        }
        response1 = client.post("/api/appointments", json=payload1)
        assert response1.status_code == 201
        appt1_id = response1.json()["id"]

        payload2 = {
            "student_id": s1.id,
            "coach_id": test_coach.id,
            "start_time": future2.isoformat(),
            "end_time": (future2 + timedelta(hours=2)).isoformat(),
        }
        response2 = client.post("/api/appointments", json=payload2)
        assert response2.status_code == 201
        appt2_id = response2.json()["id"]

        cancel_response = client.post(f"/api/appointments/{appt1_id}/cancel", json={"reason": "调整前取消"})
        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == AppointmentStatus.cancelled

        summary_before = client.get("/api/dashboard/summary").json()
        assert summary_before["active_bookings"] == 1
        assert summary_before["cancel_rule"]["min_hours_before_start"] == 2

        cancel_rule.min_hours_before_start = 4
        cancel_rule.max_active_bookings_per_student = 1
        cancel_rule.allow_cancel_completed = True

        payload3 = {
            "student_id": s1.id,
            "coach_id": test_coach.id,
            "start_time": future3.isoformat(),
            "end_time": (future3 + timedelta(hours=2)).isoformat(),
        }
        response3 = client.post("/api/appointments", json=payload3)
        assert response3.status_code == 400
        assert "Student has reached active booking limit" in response3.json()["detail"]

        near_future = datetime.now() + timedelta(hours=3)
        payload4 = {
            "student_id": s1.id,
            "coach_id": test_coach.id,
            "start_time": near_future.isoformat(),
            "end_time": (near_future + timedelta(hours=1)).isoformat(),
        }
        response4 = client.post("/api/appointments", json=payload4)
        assert response4.status_code == 400

        cancel_rule.max_active_bookings_per_student = 5
        response5 = client.post("/api/appointments", json=payload4)
        assert response5.status_code == 201
        appt3_id = response5.json()["id"]

        response6 = client.post(f"/api/appointments/{appt3_id}/cancel", json={"reason": "临近取消"})
        assert response6.status_code == 400
        assert "at least 4 hours in advance" in response6.json()["detail"]

        far_future = datetime.now() + timedelta(hours=5)
        payload5 = {
            "student_id": s1.id,
            "coach_id": test_coach.id,
            "start_time": far_future.isoformat(),
            "end_time": (far_future + timedelta(hours=1)).isoformat(),
        }
        response7 = client.post("/api/appointments", json=payload5)
        assert response7.status_code == 201
        appt4_id = response7.json()["id"]

        response8 = client.post(f"/api/appointments/{appt4_id}/cancel", json={"reason": "正常取消"})
        assert response8.status_code == 200

        past_completed = datetime.now() - timedelta(days=2)
        from app.models import Appointment
        from app.store import appointments as appts_store
        completed_appt = Appointment(
            id=next_id("appointment"),
            student_id=s1.id,
            coach_id=test_coach.id,
            start_time=past_completed,
            end_time=past_completed + timedelta(hours=2),
            status=AppointmentStatus.completed,
            created_at=past_completed - timedelta(days=1),
        )
        appts_store[completed_appt.id] = completed_appt

        response9 = client.post(f"/api/appointments/{completed_appt.id}/cancel", json={"reason": "取消已完成"})
        assert response9.status_code == 200
        assert response9.json()["status"] == AppointmentStatus.cancelled

        stats = client.get("/api/dashboard/lesson-stats").json()
        s1_stats = next(item for item in stats if item["student_id"] == s1.id)
        assert s1_stats["booked_hours"] == 3.0
        assert s1_stats["cancelled_count"] == 3

        summary_after = client.get("/api/dashboard/summary").json()
        assert summary_after["cancel_rule"]["min_hours_before_start"] == 4
        assert summary_after["cancel_rule"]["max_active_bookings_per_student"] == 5
        assert summary_after["cancel_rule"]["allow_cancel_completed"] is True

    def test_conflict_detection_works_after_rule_changes(self, client, test_student, test_coach, future_slot):
        cancel_rule.min_hours_before_start = 6
        cancel_rule.max_active_bookings_per_student = 10

        payload1 = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        client.post("/api/appointments", json=payload1)

        payload2 = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot + timedelta(hours=1)).isoformat(),
            "end_time": (future_slot + timedelta(hours=3)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload2)
        assert response.status_code == 409

    def test_hours_check_works_after_rule_changes(self, client, test_coach, future_slot):
        cancel_rule.min_hours_before_start = 1
        cancel_rule.max_active_bookings_per_student = 10

        s = Student(id=next_id("student"), name="规则后课时测试", phone="13800000402", remaining_hours=1)
        students[s.id] = s

        payload = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 400
        assert "Student does not have enough remaining hours" in response.json()["detail"]

    def test_max_active_bookings_rule_change(self, client, test_student, test_coach, future_slot):
        cancel_rule.max_active_bookings_per_student = 1

        payload1 = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=1)).isoformat(),
        }
        client.post("/api/appointments", json=payload1)

        payload2 = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot + timedelta(hours=2)).isoformat(),
            "end_time": (future_slot + timedelta(hours=3)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload2)
        assert response.status_code == 400
        assert "Student has reached active booking limit" in response.json()["detail"]

        cancel_rule.max_active_bookings_per_student = 2
        response2 = client.post("/api/appointments", json=payload2)
        assert response2.status_code == 201
