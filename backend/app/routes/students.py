from fastapi import APIRouter

from app.models import Student
from app.schemas import StudentCreate, StudentRead
from app.store import next_id, students

router = APIRouter()


@router.get("", response_model=list[StudentRead])
def list_students() -> list[Student]:
    return list(students.values())


@router.post("", response_model=StudentRead, status_code=201)
def create_student(payload: StudentCreate) -> Student:
    data = payload.model_dump()
    data["initial_hours"] = round(payload.remaining_hours, 1)
    data["remaining_hours"] = round(payload.remaining_hours, 1)
    student = Student(id=next_id("student"), **data)
    students[student.id] = student
    return student
