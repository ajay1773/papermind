from pydantic import BaseModel, Field


class SelectedPaper(BaseModel):
    openalex_id: str = Field(description="Openalex id of the paper")
    relevance_reason: str = Field(
        description="one sentence, which specific sub-question this paper addresses"
    )
    fetch_priority: str = Field(
        description="string high or low, so you know which papers to process first if you want to add that later"
    )


class SelectAndFetchOutputStructure(BaseModel):
    selected_papers: list[SelectedPaper]
