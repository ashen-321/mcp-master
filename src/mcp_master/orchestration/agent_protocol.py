from pydantic import BaseModel


class MultiAgentState(BaseModel):
    question: str
    external_data: list
    external_summaries: list
    data_sources: list
    qa_instructions: str
    qa_assessment: str
    answer: str
    tools_requested: list
