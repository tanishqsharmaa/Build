"""Pydantic schema for Agent 4 — Weekly Progress Report."""

from pydantic import BaseModel, Field, model_validator


class WeeklyReport(BaseModel):
    """Structured output from Agent 4 — Weekly Progress Report."""

    week_start: str = Field(
        ..., description="ISO date string (YYYY-MM-DD) for Monday of the report week"
    )
    milestones_completed: int = Field(
        ..., ge=0, description="Number of milestones completed this week"
    )
    avg_quiz_score: float = Field(
        ..., ge=0.0, le=100.0, description="Average quiz score across the week's submissions"
    )
    linkedin_post_text: str = Field(
        ..., min_length=20, description="AI-generated LinkedIn post text (100-150 words)"
    )
    report_html: str = Field(
        ..., min_length=20, description="Full HTML email body for the weekly digest"
    )

    @model_validator(mode="after")
    def reasonable_numbers(self) -> "WeeklyReport":
        if self.milestones_completed > 7:
            raise ValueError(
                f"milestones_completed cannot exceed 7 (one per day): {self.milestones_completed}"
            )
        return self
