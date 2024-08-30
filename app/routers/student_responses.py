from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from app.models.schemas import ProcessExamRequest
from app.services.db_services import exam_results_collection
from app.routers.marking import mark_student_response
from app.models.schemas import MarkRequest

router = APIRouter()

@router.post("/process_exam_responses")
async def process_exam_responses(request: ProcessExamRequest) -> Dict:
    results = {}
    total_marks = 0
    
    # Collect all unique learning objectives
    all_objectives = set()
    for question in request.exam_questions.get('questions', []):
        all_objectives.update(question.get('learning_objectives', []))
    
    marks_per_objective = {obj: 0 for obj in all_objectives}
    total_marks_per_objective = {obj: 0 for obj in all_objectives}

    for question, response in zip(request.exam_questions.get('questions', []), request.student_responses):
        # Handle potential missing keys
        question_number = question.get('number', 'Unknown')
        question_marks = question.get('marks', 0)
        question_objectives = question.get('learning_objectives', [])

        marking_result = await mark_student_response(MarkRequest(
            question=question, student_response=response, student_name=request.student_name, student_id=request.student_id, class_id=request.class_id))
        results[question_number] = marking_result
        marks_awarded = marking_result.get('marks_awarded', 0)
        total_marks += marks_awarded

        for obj in question_objectives:
            marks_per_objective[obj] += marks_awarded
            total_marks_per_objective[obj] += question_marks

    performance_per_objective = {
        obj: {
            "raw_score": marks_per_objective[obj],
            "total_available": total_marks_per_objective[obj],
            "percentage": (marks_per_objective[obj] / total_marks_per_objective[obj]) * 100 if total_marks_per_objective[obj] > 0 else 0
        } for obj in marks_per_objective
    }

    exam_result =  {
        "student_name": request.student_name,
        "student_id": request.student_id,
        "class_id": request.class_id,
        "total_marks": total_marks,
        "results_per_question": results,
        "performance_per_objective": performance_per_objective
    } 

 # Save the exam result to MongoDB
    result = await exam_results_collection.insert_one(exam_result)
    
    # Convert ObjectId to string for returning to the client
    exam_result["_id"] = str(result.inserted_id)

    return exam_result


# Add more routes related to student responses...
@router.get("/exam_results/{exam_id}", response_model=Dict)
async def get_exam_results(exam_id: str):
    try:
        # Convert the exam_id to an ObjectId
        exam_object_id = ObjectId(exam_id)

        # Query the database for the exam result
        exam_result = await exam_results_collection.find_one({"_id": exam_object_id})

        # If no result is found, raise an exception
        if not exam_result:
            raise HTTPException(status_code=404, detail="Exam result not found")

        # Convert ObjectId to string for returning to the client
        exam_result["_id"] = str(exam_result["_id"])

        return exam_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
