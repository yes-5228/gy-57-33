from fastapi import APIRouter, HTTPException, status

from app.models import Coach
from app.schemas import CoachCreate, CoachRead
from app.store import coaches, next_id

router = APIRouter()


@router.get("", response_model=list[CoachRead])
def list_coaches(active: bool | None = None) -> list[Coach]:
    values = list(coaches.values())
    if active is not None:
        values = [coach for coach in values if coach.active == active]
    return values


@router.post("", response_model=CoachRead, status_code=201)
def create_coach(payload: CoachCreate) -> Coach:
    coach = Coach(id=next_id("coach"), **payload.model_dump())
    coaches[coach.id] = coach
    return coach


@router.patch("/{coach_id}/active", response_model=CoachRead)
def update_coach_active(coach_id: int, active: bool) -> Coach:
    coach = coaches.get(coach_id)
    if not coach:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Coach not found")
    coach.active = active
    coaches[coach.id] = coach
    return coach
