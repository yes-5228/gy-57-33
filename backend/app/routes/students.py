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
    student = Student(id=next_id("student"), **payload.model_dump())
    students[student.id] = student
    return student
