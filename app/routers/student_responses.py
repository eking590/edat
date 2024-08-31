from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from bson import ObjectId
from app.models.schemas import ProcessExamRequest
from app.services.db_services import exam_results_collection
from app.services.db_services import student_response_collection
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




#generate exam result using student_id 
@router.get("/exam_results/student/{student_id}", response_model=List[Dict])
async def get_exam_results_by_student(student_id: str):
    try:
        # Query the database for all exam results associated with the given student_id
        exam_results = await exam_results_collection.find({"student_id": student_id}).to_list(length=None)

        # If no results are found, raise an exception
        if not exam_results:
            raise HTTPException(status_code=404, detail="No exam results found for this student")

        # Convert ObjectId fields to strings for returning to the client
        for exam_result in exam_results:
            exam_result["_id"] = str(exam_result["_id"])

        return exam_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



#process exam result using student_id
@router.get("/process_exam_result/{student_id}")
async def process_exam_result(student_id: str) -> Dict:
    # Fetch all responses for the student from the database
    student_responses = await student_response_collection.find({"student_id": student_id}).to_list(length=None)

    if not student_responses:
        raise HTTPException(status_code=404, detail="No responses found for the given student ID.")

    total_marks = 0
    all_objectives = set()
    marks_per_objective = {}
    total_marks_per_objective = {}

    # Initialize objectives and total marks
    for response in student_responses:
        question_objectives = response['question'].get('learning_objectives', [])
        all_objectives.update(question_objectives)

    # Initialize marks per objective
    for obj in all_objectives:
        marks_per_objective[obj] = 0
        total_marks_per_objective[obj] = 0

    results_per_question = {}
    
    # Process each response to calculate the exam result
    for response in student_responses:
        question_number = response['question'].get('number', 'Unknown')
        question_marks = response['question'].get('marks', 0)
        question_objectives = response['question'].get('learning_objectives', [])
        marks_awarded = response.get('marks_awarded', 0)
        feedback = response.get('feedback', '')
        justification = response.get('justification', '')

        results_per_question[question_number] = {
            "marks_awarded": marks_awarded,
            "feedback": feedback,
            "justification": justification
        }
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

    exam_result = {
        "student_name": student_responses[0].get("student_name"),
        "student_id": student_id,
        "class_id": student_responses[0].get("class_id"),
        "total_marks": total_marks,
        "results_per_question": results_per_question,
        "performance_per_objective": performance_per_objective
    }

    # Store the processed exam result in MongoDB
    result = await exam_results_collection.insert_one(exam_result)

    # Convert ObjectId to string for returning to the client
    exam_result["_id"] = str(result.inserted_id)

    return exam_result