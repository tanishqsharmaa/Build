"""GET /report/{user_id} — weekly progress report stub.

Agent 4 (Progress Report) is implemented in Sprint 8.
This stub keeps the router skeleton in place so the test suite
and frontend API contract don't break.
"""
from fastapi import APIRouter

from src.api.schemas import ReportResponse

router = APIRouter()


@router.get("/{user_id}", response_model=ReportResponse)
async def get_report(user_id: str) -> ReportResponse:  # noqa: ARG001
    """Stub — returns 200 with a placeholder message until Sprint 8."""
    return ReportResponse(message="Not implemented — Sprint 8")
