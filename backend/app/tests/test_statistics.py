from datetime import datetime, timedelta

import pytest

from app.models import AppointmentStatus, Student
from app.store import cancel_rule, next_id, students


class TestDashboardSummary:
    def test_empty_dashboard_summary(self, client):
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_students"] == 0
        assert data["total_coaches"] == 0
        assert data["active_bookings"] == 0
        assert data["completed_hours"] == 0.0
        assert data["cancel_rule"]["min_hours_before_start"] == 2
        assert data["cancel_rule"]["max_active_bookings_per_student"] == 3
        assert data["cancel_rule"]["allow_cancel_completed"] is False

    def test_summary_with_data(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, hours=2)
        past = datetime.now() - timedelta(days=2)
        create_booking(test_student.id, test_coach.id, past, hours=3, status=AppointmentStatus.completed)

        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_students"] == 1
        assert data["total_coaches"] == 1
        assert data["active_bookings"] == 1
        assert data["completed_hours"] == 3.0

    def test_summary_cancel_rule_reflects_changes(self, client):
        cancel_rule.min_hours_before_start = 6
        cancel_rule.max_active_bookings_per_student = 5
        cancel_rule.allow_cancel_completed = True

        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["cancel_rule"]["min_hours_before_start"] == 6
        assert data["cancel_rule"]["max_active_bookings_per_student"] == 5
        assert data["cancel_rule"]["allow_cancel_completed"] is True

    def test_summary_multiple_students_coaches(self, client, test_coach, test_coach2, future_slot, create_booking):
        s1 = Student(id=next_id("student"), name="学员1", phone="13800000201", remaining_hours=10)
        s2 = Student(id=next_id("student"), name="学员2", phone="13800000202", remaining_hours=15)
        s3 = Student(id=next_id("student"), name="学员3", phone="13800000203", remaining_hours=5)
        students[s1.id] = s1
        students[s2.id] = s2
        students[s3.id] = s3

        create_booking(s1.id, test_coach.id, future_slot, hours=2)
        create_booking(s2.id, test_coach2.id, future_slot + timedelta(hours=3), hours=1)
        past = datetime.now() - timedelta(days=1)
        create_booking(s3.id, test_coach.id, past, hours=2, status=AppointmentStatus.completed)
        create_booking(s1.id, test_coach2.id, past - timedelta(days=1), hours=3, status=AppointmentStatus.completed)

        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_students"] == 3
        assert data["total_coaches"] == 2
        assert data["active_bookings"] == 2
        assert data["completed_hours"] == 5.0

    def test_summary_only_cancelled_bookings(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, status=AppointmentStatus.cancelled)

        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["active_bookings"] == 0
        assert data["completed_hours"] == 0.0

    def test_summary_fractional_completed_hours(self, client, test_student, test_coach, create_booking):
        past = datetime.now() - timedelta(days=1)
        create_booking(test_student.id, test_coach.id, past, hours=1.5, status=AppointmentStatus.completed)
        create_booking(test_student.id, test_coach.id, past - timedelta(days=1), hours=2.5, status=AppointmentStatus.completed)

        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["completed_hours"] == 4.0


class TestLessonStats:
    def test_empty_lesson_stats(self, client):
        response = client.get("/api/dashboard/lesson-stats")
        assert response.status_code == 200
        assert response.json() == []

    def test_lesson_stats_single_student_no_bookings(self, client, test_student):
        response = client.get("/api/dashboard/lesson-stats")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["student_id"] == test_student.id
        assert data[0]["student_name"] == test_student.name
        assert data[0]["completed_hours"] == 0.0
        assert data[0]["booked_hours"] == 0.0
        assert data[0]["cancelled_count"] == 0
        assert data[0]["remaining_hours"] == test_student.remaining_hours

    def test_lesson_stats_with_all_statuses(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, hours=2)
        past = datetime.now() - timedelta(days=1)
        create_booking(test_student.id, test_coach.id, past, hours=3, status=AppointmentStatus.completed)
        create_booking(test_student.id, test_coach.id, future_slot + timedelta(days=1), hours=1, status=AppointmentStatus.cancelled)

        response = client.get("/api/dashboard/lesson-stats")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["completed_hours"] == 3.0
        assert data[0]["booked_hours"] == 2.0
        assert data[0]["cancelled_count"] == 1

    def test_lesson_stats_multiple_students(self, client, test_coach, future_slot, create_booking):
        s1 = Student(id=next_id("student"), name="学员A", phone="13800000301", remaining_hours=20)
        s2 = Student(id=next_id("student"), name="学员B", phone="13800000302", remaining_hours=10)
        students[s1.id] = s1
        students[s2.id] = s2

        create_booking(s1.id, test_coach.id, future_slot, hours=2)
        past = datetime.now() - timedelta(days=2)
        create_booking(s1.id, test_coach.id, past, hours=4, status=AppointmentStatus.completed)
        create_booking(s2.id, test_coach.id, future_slot + timedelta(hours=3), hours=1, status=AppointmentStatus.cancelled)
        create_booking(s2.id, test_coach.id, past - timedelta(days=1), hours=2, status=AppointmentStatus.completed)

        response = client.get("/api/dashboard/lesson-stats")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        s1_stats = next(item for item in data if item["student_id"] == s1.id)
        s2_stats = next(item for item in data if item["student_id"] == s2.id)

        assert s1_stats["completed_hours"] == 4.0
        assert s1_stats["booked_hours"] == 2.0
        assert s1_stats["cancelled_count"] == 0
        assert s1_stats["remaining_hours"] == 20

        assert s2_stats["completed_hours"] == 2.0
        assert s2_stats["booked_hours"] == 0.0
        assert s2_stats["cancelled_count"] == 1
        assert s2_stats["remaining_hours"] == 10

    def test_lesson_stats_fractional_hours(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, hours=1.5)
        past = datetime.now() - timedelta(days=1)
        create_booking(test_student.id, test_coach.id, past, hours=2.5, status=AppointmentStatus.completed)

        response = client.get("/api/dashboard/lesson-stats")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["completed_hours"] == 2.5
        assert data[0]["booked_hours"] == 1.5

    def test_lesson_stats_hours_rounding(self, client, test_student, test_coach, create_booking):
        past = datetime.now() - timedelta(days=1)
        create_booking(test_student.id, test_coach.id, past, hours=1.333, status=AppointmentStatus.completed)
        create_booking(test_student.id, test_coach.id, past - timedelta(days=1), hours=2.666, status=AppointmentStatus.completed)

        response = client.get("/api/dashboard/lesson-stats")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["completed_hours"] == 4.0

    def test_lesson_stats_multiple_cancellations(self, client, test_student, test_coach, future_slot, create_booking):
        for i in range(3):
            create_booking(
                test_student.id,
                test_coach.id,
                future_slot + timedelta(days=i),
                status=AppointmentStatus.cancelled,
            )

        response = client.get("/api/dashboard/lesson-stats")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["cancelled_count"] == 3

    def test_lesson_stats_includes_inactive_coach_bookings(self, client, test_student, inactive_coach, future_slot, create_booking):
        create_booking(test_student.id, inactive_coach.id, future_slot, hours=2)

        response = client.get("/api/dashboard/lesson-stats")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["booked_hours"] == 2.0


class TestStatsAfterRuleChanges:
    def test_stats_consistent_after_cancel_rule_change(self, client, test_student, test_coach, future_slot, create_booking):
        create_booking(test_student.id, test_coach.id, future_slot, hours=2)
        past = datetime.now() - timedelta(days=1)
        create_booking(test_student.id, test_coach.id, past, hours=3, status=AppointmentStatus.completed)

        cancel_rule.min_hours_before_start = 4
        cancel_rule.max_active_bookings_per_student = 1
        cancel_rule.allow_cancel_completed = True

        response = client.get("/api/dashboard/lesson-stats")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["completed_hours"] == 3.0
        assert data[0]["booked_hours"] == 2.0

        summary = client.get("/api/dashboard/summary").json()
        assert summary["cancel_rule"]["min_hours_before_start"] == 4
        assert summary["cancel_rule"]["max_active_bookings_per_student"] == 1
