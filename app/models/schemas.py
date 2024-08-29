from pydantic import BaseModel
from typing import Dict, List, Optional

class ExamRequest(BaseModel):
    role: str  # Role can be 'parent' or 'teacher
    exam_board: str
    country: str
    learning_objectives: List[str]
    subject: str
    exam_length: Optional[int] = None
    num_questions: int = 5
    total_marks: Optional[int] = None
    student_id: Optional[str] = None  # Student ID should be optional
    class_id: Optional[str] = None  # Class ID should be optional

class MarkRequest(BaseModel):
    question: Dict
    student_response: str
    student_name: str
    student_id: str
    class_id: str

class ProcessExamRequest(BaseModel):
    exam_questions: Dict
    student_responses: List[str]
    student_name: str
    student_id: str
    class_id: str

# Add other models here...
