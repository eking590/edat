from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import json 
from app.models.schemas import MarkRequest
from app.services.api_service import api_request
from app.services.db_services import student_response_collection, exam_results_collection

router = APIRouter()

@router.post("/mark_student_response")
async def mark_student_response(request: MarkRequest) -> Dict:
    context = f"""
    Mark the following student response based on the given question and mark scheme. Never award marks for things like neatness and presentation:

    Student Name: {request.student_name}
    Student Id: {request.student_id}
    Class Id: {request.class_id}
    Question: {request.question['text']}
    Marks available: {request.question['marks']}
    Mark Scheme: {request.question['mark_scheme']}

    Student Response: {request.student_response}

    Please provide:
    1. The marks awarded. Ensure that marks are awarded for only questions they are intended for
    2. Detailed examiner-style feedback, **provide only feedback**. **There never be any salutation e.g. dear ..., hi...**. You can address the student in second person speak using something like 'you'
    3. Justification for the marks given
    
    Format the output as a JSON object with the following structure:
    {{
        "marks_awarded": 0,
        "feedback": "Detailed feedback",
        "justification": "Justification for marks"
    }}
    """

    messages = [{"role": "user", "content": context}]
    response_text = api_request(messages, 1000)
    
    try:
         # Parse the response from the API
        response_data = json.loads(response_text)

        #return json.loads(response_text)

        # Prepare the data to be stored in the database
        student_response_data = {
            "student_name": request.student_name,
            "student_id": request.student_id,
            "class_id": request.class_id,
            "question": request.question,
            "student_response": request.student_response,
            "marks_awarded": response_data.get("marks_awarded"),
            "feedback": response_data.get("feedback"),
            "justification": response_data.get("justification"),
        }

        # Store the student response in MongoDB
        result = await student_response_collection.insert_one(student_response_data)

        # Convert ObjectId to string for returning to the client
        student_response_data["_id"] = str(result.inserted_id)
        
        return student_response_data
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail="Failed to parse JSON response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

# Add more routes related to marking...
@router.get("/process_student_results/{student_id}")
async def process_student_results(student_id: str) -> Dict:
    # Step 1: Fetch all responses for the student from the database
    student_responses = await student_response_collection.find({"student_id": student_id}).to_list(length=None)

    if not student_responses:
        raise HTTPException(status_code=404, detail="No responses found for the given student ID.")

    total_marks = 0
    all_objectives = set()
    marks_per_objective = {}
    total_marks_per_objective = {}

    # Step 2: Initialize objectives and total marks
    for response in student_responses:
        question_objectives = response['question'].get('learning_objectives', [])
        all_objectives.update(question_objectives)

    # Initialize marks per objective
    for obj in all_objectives:
        marks_per_objective[obj] = 0
        total_marks_per_objective[obj] = 0

    results_per_question = {}

    # Step 3: Process each response to calculate the exam result
    for response in student_responses:
        question_number = response['question'].get('number', 'Unknown')
        question_marks = response['question'].get('marks', 0)
        question_objectives = response['question'].get('learning_objectives', [])
        marks_awarded = response.get('marks_awarded', 0)
        feedback = response.get('feedback', '')
        justification = response.get('justification', '')

        # Record the results per question
        results_per_question[question_number] = {
            "marks_awarded": marks_awarded,
            "feedback": feedback,
            "justification": justification
        }
        total_marks += marks_awarded

        # Aggregate marks per learning objective
        for obj in question_objectives:
            marks_per_objective[obj] += marks_awarded
            total_marks_per_objective[obj] += question_marks

    # Calculate performance per learning objective
    performance_per_objective = {
        obj: {
            "raw_score": marks_per_objective[obj],
            "total_available": total_marks_per_objective[obj],
            "percentage": (marks_per_objective[obj] / total_marks_per_objective[obj]) * 100 if total_marks_per_objective[obj] > 0 else 0
        } for obj in marks_per_objective
    }

    # Prepare the exam result data
    exam_result = {
        "student_name": student_responses[0].get("student_name"),
        "student_id": student_id,
        "class_id": student_responses[0].get("class_id"),
        "total_marks": total_marks,
        "results_per_question": results_per_question,
        "performance_per_objective": performance_per_objective
    }

    # Step 4: Store the processed exam result in MongoDB
    result = await exam_results_collection.insert_one(exam_result)

    # Convert ObjectId to string for returning to the client
    exam_result["_id"] = str(result.inserted_id)

    # Step 5: Return the processed exam result
    return exam_result