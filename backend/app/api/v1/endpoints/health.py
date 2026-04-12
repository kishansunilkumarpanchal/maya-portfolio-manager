from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="maya-portfolio-manager-backend")

