from datetime import datetime, timedelta

import pytest

from app.models import AppointmentStatus, Student
from app.store import cancel_rule, next_id, students


class TestHoursRefundOnCancellation:
    def test_cancel_refund_exact_hours(self, client, test_student, test_coach, future_slot):
        original_hours = test_student.remaining_hours

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        book_response = client.post("/api/appointments", json=payload)
        assert book_response.status_code == 201
        appt_id = book_response.json()["id"]

        after_booking = client.get("/api/dashboard/lesson-stats").json()
        student_after_booking = next(s for s in after_booking if s["student_id"] == test_student.id)
        assert student_after_booking["remaining_hours"] == original_hours - 2

        cancel_response = client.post(f"/api/appointments/{appt_id}/cancel", json={"reason": "退款测试"})
        assert cancel_response.status_code == 200

        after_cancel = client.get("/api/dashboard/lesson-stats").json()
        student_after_cancel = next(s for s in after_cancel if s["student_id"] == test_student.id)
        assert student_after_cancel["remaining_hours"] == original_hours

    def test_cancel_refund_fractional_hours(self, client, test_coach, future_slot):
        s = Student(id=next_id("student"), name="小数课时学员", phone="13800000501", remaining_hours=10)
        students[s.id] = s
        original_hours = s.remaining_hours

        payload = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=1, minutes=30)).isoformat(),
        }
        book_response = client.post("/api/appointments", json=payload)
        assert book_response.status_code == 201
        appt_id = book_response.json()["id"]

        after_booking = client.get("/api/dashboard/lesson-stats").json()
        student_after_booking = next(x for x in after_booking if x["student_id"] == s.id)
        assert student_after_booking["remaining_hours"] == original_hours - 1.5

        cancel_response = client.post(f"/api/appointments/{appt_id}/cancel", json={"reason": "小数退款"})
        assert cancel_response.status_code == 200

        after_cancel = client.get("/api/dashboard/lesson-stats").json()
        student_after_cancel = next(x for x in after_cancel if x["student_id"] == s.id)
        assert student_after_cancel["remaining_hours"] == original_hours

    def test_refund_matches_deducted_amount(self, client, test_student, test_coach, future_slot):
        cancel_rule.max_active_bookings_per_student = 10
        hours_list = [1, 2, 3, 4]
        booked_ids = []
        offset = 0

        for hours in hours_list:
            start = future_slot + timedelta(hours=offset)
            end = start + timedelta(hours=hours)
            payload = {
                "student_id": test_student.id,
                "coach_id": test_coach.id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            }
            response = client.post("/api/appointments", json=payload)
            assert response.status_code == 201
            booked_ids.append(response.json()["id"])
            offset += hours + 1

        before_cancel_stats = client.get("/api/dashboard/lesson-stats").json()
        before_cancel_hours = next(s for s in before_cancel_stats if s["student_id"] == test_student.id)["remaining_hours"]

        for appt_id in booked_ids:
            client.post(f"/api/appointments/{appt_id}/cancel", json={"reason": "全部取消"})

        after_cancel_stats = client.get("/api/dashboard/lesson-stats").json()
        after_cancel_hours = next(s for s in after_cancel_stats if s["student_id"] == test_student.id)["remaining_hours"]

        assert after_cancel_hours == before_cancel_hours + sum(hours_list)
        assert after_cancel_hours == test_student.remaining_hours

    def test_cancel_completed_refund_when_allowed(self, client, test_student, test_coach, create_booking):
        cancel_rule.allow_cancel_completed = True
        original_hours = test_student.remaining_hours

        past = datetime.now() - timedelta(days=2)
        appt = create_booking(test_student.id, test_coach.id, past, hours=2, status=AppointmentStatus.completed)

        before_stats = client.get("/api/dashboard/lesson-stats").json()
        before_hours = next(s for s in before_stats if s["student_id"] == test_student.id)["remaining_hours"]

        response = client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "完成后取消"})
        assert response.status_code == 200

        after_stats = client.get("/api/dashboard/lesson-stats").json()
        after_hours = next(s for s in after_stats if s["student_id"] == test_student.id)["remaining_hours"]
        assert after_hours == before_hours + 2

    def test_cancel_then_rebook_uses_refunded_hours(self, client, test_coach, future_slot):
        s = Student(id=next_id("student"), name="重复预约学员", phone="13800000502", remaining_hours=2)
        students[s.id] = s

        payload1 = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        book1 = client.post("/api/appointments", json=payload1)
        assert book1.status_code == 201
        appt1_id = book1.json()["id"]

        payload2 = {
            "student_id": s.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot + timedelta(days=1)).isoformat(),
            "end_time": (future_slot + timedelta(days=1, hours=2)).isoformat(),
        }
        book2_fail = client.post("/api/appointments", json=payload2)
        assert book2_fail.status_code == 400

        client.post(f"/api/appointments/{appt1_id}/cancel", json={"reason": "改期"})

        book2_success = client.post("/api/appointments", json=payload2)
        assert book2_success.status_code == 201

    def test_already_cancelled_no_double_refund(self, client, test_student, test_coach, future_slot, create_booking):
        original_hours = test_student.remaining_hours

        appt = create_booking(test_student.id, test_coach.id, future_slot, hours=2, status=AppointmentStatus.booked)

        client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "首次取消"})
        after_first_cancel = client.get("/api/dashboard/lesson-stats").json()
        hours_after_first = next(s for s in after_first_cancel if s["student_id"] == test_student.id)["remaining_hours"]

        client.post(f"/api/appointments/{appt.id}/cancel", json={"reason": "二次取消"})
        after_second_cancel = client.get("/api/dashboard/lesson-stats").json()
        hours_after_second = next(s for s in after_second_cancel if s["student_id"] == test_student.id)["remaining_hours"]

        assert hours_after_first == hours_after_second

    def test_stats_refresh_immediately_after_cancel(self, client, test_student, test_coach, future_slot):
        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=3)).isoformat(),
        }
        book_resp = client.post("/api/appointments", json=payload)
        assert book_resp.status_code == 201
        appt_id = book_resp.json()["id"]

        stats_before = client.get("/api/dashboard/lesson-stats").json()
        hours_before = next(s for s in stats_before if s["student_id"] == test_student.id)["remaining_hours"]

        cancel_resp = client.post(f"/api/appointments/{appt_id}/cancel", json={"reason": "立即刷新测试"})
        assert cancel_resp.status_code == 200

        stats_after = client.get("/api/dashboard/lesson-stats").json()
        hours_after = next(s for s in stats_after if s["student_id"] == test_student.id)["remaining_hours"]

        assert hours_after == hours_before + 3

        dashboard_after = client.get("/api/dashboard/summary").json()
        assert dashboard_after["active_bookings"] == 0


class TestStudentTimeConflict:
    def test_same_student_same_time_different_coach_conflict(self, client, test_student, test_coach, test_coach2, future_slot):
        payload1 = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response1 = client.post("/api/appointments", json=payload1)
        assert response1.status_code == 201

        payload2 = {
            "student_id": test_student.id,
            "coach_id": test_coach2.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response2 = client.post("/api/appointments", json=payload2)
        assert response2.status_code == 409
        assert "time slot" in response2.json()["detail"].lower() or "conflict" in response2.json()["detail"].lower() or "时间" in response2.json()["detail"]

    def test_same_student_partial_overlap_different_coach(self, client, test_student, test_coach, test_coach2, future_slot):
        payload1 = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        client.post("/api/appointments", json=payload1)

        payload2 = {
            "student_id": test_student.id,
            "coach_id": test_coach2.id,
            "start_time": (future_slot + timedelta(hours=1)).isoformat(),
            "end_time": (future_slot + timedelta(hours=3)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload2)
        assert response.status_code == 409

    def test_same_student_contained_overlap_different_coach(self, client, test_student, test_coach, test_coach2, future_slot):
        payload1 = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=3)).isoformat(),
        }
        client.post("/api/appointments", json=payload1)

        payload2 = {
            "student_id": test_student.id,
            "coach_id": test_coach2.id,
            "start_time": (future_slot + timedelta(minutes=30)).isoformat(),
            "end_time": (future_slot + timedelta(hours=1, minutes=30)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload2)
        assert response.status_code == 409

    def test_same_student_contains_existing_different_coach(self, client, test_student, test_coach, test_coach2, future_slot):
        payload1 = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": (future_slot + timedelta(hours=1)).isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        client.post("/api/appointments", json=payload1)

        payload2 = {
            "student_id": test_student.id,
            "coach_id": test_coach2.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=3)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload2)
        assert response.status_code == 409

    def test_same_student_adjacent_no_conflict(self, client, test_student, test_coach, test_coach2, future_slot):
        payload1 = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        client.post("/api/appointments", json=payload1)

        payload2 = {
            "student_id": test_student.id,
            "coach_id": test_coach2.id,
            "start_time": (future_slot + timedelta(hours=2)).isoformat(),
            "end_time": (future_slot + timedelta(hours=4)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload2)
        assert response.status_code == 201

    def test_same_student_no_conflict_cancelled_booking(self, client, test_student, test_coach, test_coach2, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, status=AppointmentStatus.cancelled)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach2.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_same_student_no_conflict_completed_booking(self, client, test_student, test_coach, test_coach2, future_slot, create_booking):
        past = datetime.now() - timedelta(days=1)
        create_booking(test_student.id, test_coach.id, past, status=AppointmentStatus.completed)

        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach2.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload)
        assert response.status_code == 201

    def test_duplicate_submission_returns_conflict(self, client, test_student, test_coach, test_coach2, future_slot):
        payload = {
            "student_id": test_student.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        client.post("/api/appointments", json=payload)

        payload_dup = {
            "student_id": test_student.id,
            "coach_id": test_coach2.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response = client.post("/api/appointments", json=payload_dup)
        assert response.status_code == 409

    def test_different_students_same_time_no_conflict(self, client, test_coach, test_coach2, future_slot):
        s1 = Student(id=next_id("student"), name="学员甲", phone="13800000601", remaining_hours=10)
        s2 = Student(id=next_id("student"), name="学员乙", phone="13800000602", remaining_hours=10)
        students[s1.id] = s1
        students[s2.id] = s2

        payload1 = {
            "student_id": s1.id,
            "coach_id": test_coach.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response1 = client.post("/api/appointments", json=payload1)
        assert response1.status_code == 201

        payload2 = {
            "student_id": s2.id,
            "coach_id": test_coach2.id,
            "start_time": future_slot.isoformat(),
            "end_time": (future_slot + timedelta(hours=2)).isoformat(),
        }
        response2 = client.post("/api/appointments", json=payload2)
        assert response2.status_code == 201
