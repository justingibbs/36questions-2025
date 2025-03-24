from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Answer(BaseModel):
    question_id: int
    answer: str
    status: str = Field(default="answered", pattern="^(answered|skipped)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)

class UserAnswers(BaseModel):
    user_id: str
    answers: List[Answer] = []

class QuestionResponse(BaseModel):
    html: str
    question_id: Optional[int] 