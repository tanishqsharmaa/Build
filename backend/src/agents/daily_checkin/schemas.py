from pydantic import BaseModel, Field, model_validator


class MorningBrief(BaseModel):
    """Structured output from Agent 3a — Morning Brief Generator."""

    topic: str = Field(..., description="Today's learning topic")
    key_concepts: list[str] = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Exactly 5 key concepts, each under 20 words",
    )
    misconceptions: list[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Exactly 2 common misconceptions students have about this topic",
    )
    mnemonic: str = Field(
        ..., description="One memorable mnemonic or memory trick for the topic"
    )
    think_about: list[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 thought-provoking questions for the student to ponder",
    )

    @model_validator(mode="after")
    def concepts_under_20_words(self) -> "MorningBrief":
        for concept in self.key_concepts:
            word_count = len(concept.split())
            if word_count > 20:
                raise ValueError(
                    f"key_concept exceeds 20 words ({word_count} words): '{concept}'"
                )
        return self
