from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import json 
from app.models.schemas import MarkRequest
from app.services.api_service import api_request
from app.services.db_services import student_response_collection

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
