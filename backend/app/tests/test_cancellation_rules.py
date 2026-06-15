from datetime import datetime, timedelta

import pytest

from app.models import AppointmentStatus
from app.store import appointments, cancel_rule, next_id


class TestCancellationRules:
    def test_cancel_with_sufficient_notice(self, client, test_student, test_coach, future_slot, create_booking):
        appt = create_booking(test_student.id, test_coach.id, future_slot)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "个人原因"})
        assert response.status_code == 200
        assert response.json()["status"] == AppointmentStatus.cancelled
        assert response.json()["cancel_reason"] == "个人原因"
        assert response.json()["cancelled_at"] is not None

    def test_cancel_less_than_min_hours_rejected(self, client, test_student, test_coach, create_booking):
        near_future = datetime.now() + timedelta(hours=1)
        appt = create_booking(test_student.id, test_coach.id, near_future)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "临时有事"})
        assert response.status_code == 400
        assert "at least 2 hours in advance" in response.json()["detail"]

    def test_cancel_exactly_at_min_hours_boundary(self, client, test_student, test_coach, create_booking):
        exact_boundary = datetime.now() + timedelta(hours=2, minutes=1)
        appt = create_booking(test_student.id, test_coach.id, exact_boundary)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "刚好边界"})
        assert response.status_code == 200

    def test_cancel_one_minute_less_than_min_hours(self, client, test_student, test_coach, create_booking):
        just_under = datetime.now() + timedelta(hours=1, minutes=59)
        appt = create_booking(test_student.id, test_coach.id, just_under)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "差一分钟"})
        assert response.status_code == 400

    def test_cancel_already_cancelled_rejected(self, client, test_student, test_coach, future_slot, create_booking):
        appt = create_booking(test_student.id, test_coach.id, future_slot, status=AppointmentStatus.cancelled)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "再次取消"})
        assert response.status_code == 400
        assert "Appointment already cancelled" in response.json()["detail"]

    def test_cancel_completed_rejected_by_default(self, client, test_student, test_coach, create_booking):
        past_time = datetime.now() - timedelta(hours=3)
        appt = create_booking(test_student.id, test_coach.id, past_time, status=AppointmentStatus.completed)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "取消已完成"})
        assert response.status_code == 400
        assert "Completed appointments cannot be cancelled" in response.json()["detail"]

    def test_cancel_completed_allowed_when_rule_enabled(self, client, test_student, test_coach, create_booking):
        cancel_rule.allow_cancel_completed = True

        past_time = datetime.now() - timedelta(hours=3)
        appt = create_booking(test_student.id, test_coach.id, past_time, status=AppointmentStatus.completed)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "特殊情况"})
        assert response.status_code == 200
        assert response.json()["status"] == AppointmentStatus.cancelled

    def test_cancel_with_custom_min_hours_rule(self, client, test_student, test_coach, create_booking):
        cancel_rule.min_hours_before_start = 4

        three_hours_later = datetime.now() + timedelta(hours=3)
        appt = create_booking(test_student.id, test_coach.id, three_hours_later)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "三小时不够"})
        assert response.status_code == 400
        assert "at least 4 hours in advance" in response.json()["detail"]

    def test_cancel_with_custom_min_hours_allowed(self, client, test_student, test_coach, create_booking):
        cancel_rule.min_hours_before_start = 4

        five_hours_later = datetime.now() + timedelta(hours=5)
        appt = create_booking(test_student.id, test_coach.id, five_hours_later)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "五小时足够"})
        assert response.status_code == 200

    def test_cancel_nonexistent_appointment(self, client):
        response = client.post("/api/appointments/9999/cancel", json={"reason": "不存在"})
        assert response.status_code == 404
        assert "Appointment not found" in response.json()["detail"]

    def test_cancel_preserves_audit_fields(self, client, test_student, test_coach, future_slot, create_booking):
        appt = create_booking(test_student.id, test_coach.id, future_slot)

        before = datetime.now()
        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "审计测试"})
        after = datetime.now()

        assert response.status_code == 200
        cancelled_at = datetime.fromisoformat(response.json()["cancelled_at"].replace("Z", "+00:00"))
        assert before.replace(tzinfo=None) <= cancelled_at.replace(tzinfo=None) <= after.replace(tzinfo=None)
        assert response.json()["cancel_reason"] == "审计测试"

    def test_cancel_uses_default_reason_when_not_provided(self, client, test_student, test_coach, future_slot, create_booking):
        appt = create_booking(test_student.id, test_coach.id, future_slot)

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={})
        assert response.status_code == 200
        assert response.json()["cancel_reason"] == "学员主动取消"
