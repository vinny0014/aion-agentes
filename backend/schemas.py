from pydantic import BaseModel, Field
from typing import Optional, List

class TaskCreate(BaseModel):
    description: str = Field(..., min_length=3)
    title: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    result: Optional[str] = None
    report: Optional[str] = None
    created_at: str
    updated_at: str

class StepOut(BaseModel):
    id: int
    task_id: int
    step_order: int
    title: str
    status: str
    details: Optional[str] = None
    created_at: str

class RunResult(BaseModel):
    task: TaskOut
    steps: List[StepOut]
    report: str
