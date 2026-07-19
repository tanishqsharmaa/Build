"""GET /report/{user_id} — weekly progress reports.

Returns the last 4 weeks of progress reports from the weekly_reports table.
"""
from fastapi import APIRouter, HTTPException

from src.api.schemas import ReportResponse
from src.db.client import get_supabase

router = APIRouter()


@router.get("/{user_id}", response_model=ReportResponse)
async def get_report(user_id: str) -> ReportResponse:
    supabase = get_supabase()
    try:
        rows = (
            supabase.table("weekly_reports")
            .select("*")
            .eq("user_id", user_id)
            .order("week_start", desc=True)
            .limit(4)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Database query failed: {exc}",
        ) from exc

    return ReportResponse(reports=rows.data if rows.data else [])
