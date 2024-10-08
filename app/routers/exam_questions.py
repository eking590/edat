from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import json 
from bson import ObjectId
from app.models.schemas import ExamRequest
from app.services.api_service import api_request
from app.services.db_services import exam_questions_collection, convert_object_id

router = APIRouter()


@router.post("/generate_exam_questions")
async def generate_exam_questions(request: ExamRequest) -> Dict:
    
     # Set student_id to None if the role is teacher, and set class_id to None if the role is parent
    if request.role == "teacher":
        request.student_id = None
    elif request.role == "parent":
        request.class_id = None

    context = f"""
    Generate {request.num_questions} examination-style questions for the following specifications:
    - Examination Board: {request.exam_board}
    - Country: {request.country}
    - Subject: {request.subject}
    - student_id: {request.student_id}
    - class_id: {request.class_id}
    - Learning Objectives: {', '.join(request.learning_objectives)} #gets the learning objectives from the database
    - Number of Questions: {request.num_questions}
    {f'- Examination Length: {request.exam_length} minutes' if request.exam_length else ''}
    {f'- Total Marks: {request.total_marks}' if request.total_marks else ''}

    Requirements:
    1. Questions should follow the {request.exam_board} examination board style and specifications.
    2. Questions can be nested (e.g., 1(a)i, 1(a)ii, 1(b), etc.) as per board expectations.
    3. All questions should be answerable by typing only.
    4. Provide a detailed mark scheme for each question.
    5. Clearly indicate the number of marks for each question or sub-question.
    6. Map each question to the relevant learning objective(s).
    7. Ensure questions and subquestions are unique.
    8. For the mark scheme, ensure you allocate marks for working out or process.
    9. Use proper mathematical notation for fractions, equations, powers, square roots, etc.
    
    Format the output as a JSON object with the following structure:
    {{
        "questions": [
            {{
                "number": "1",
                "text": "Question text",
                "marks": 5,
                "learning_objectives": ["Objective 1", "Objective 2"],
                "mark_scheme": "Detailed mark scheme"
            }},
            ...
        ]
    }}
    """

    messages = [{"role": "user", "content": context}]
    response_text =   api_request(messages, 2000)
    
    try:
        exam_questions = json.loads(response_text)

        # Add student_id and class_id to the exam_questions document
        exam_questions['student_id'] = request.student_id
        exam_questions['class_id'] = request.class_id
        
        # Store exam questions in MongoDB
     

        # Include student_id and class_id based on the role
        if request.role == "teacher":
            exam_questions['class_id'] = request.class_id
        elif request.role == "parent":
            exam_questions['student_id'] = request.student_id


        result = await exam_questions_collection.insert_one(exam_questions)
    
        # Convert ObjectId to string
        exam_questions['_id'] = str(result.inserted_id)
        
        return {"exam_question": exam_questions}
        
        #return json.loads(response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse JSON response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get("/get_exam_questions")
async def get_exam_questions(role: str, student_id: Optional[str] = None, class_id: Optional[str] = None) -> Dict:
    query = {}

    # Adjust the query based on the role
    if role == "teacher":
        if not class_id:
            raise HTTPException(status_code=400, detail="class_id is required for teachers.")
        query["class_id"] = class_id  # Teachers should provide class_id
    elif role == "parent":
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required for parents.")
        query["student_id"] = student_id  # Parents should provide student_id
    else:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'parent' or 'teacher'.")


    exam_questions = await exam_questions_collection.find(query).to_list(length=None)
    
    if not exam_questions:
        raise HTTPException(status_code=404, detail="Exam questions not found for this student.")
    
    # Convert ObjectId to string
    exam_questions = [convert_object_id(exam) for exam in exam_questions]
    

    return {"exam_questions": exam_questions}

 


#get all exams ids 
@router.get("/get_exam_ids")
async def get_exam_ids(class_id: str, user_role: str) -> Dict[str, List[str]]:
    try:
         
        if user_role != "teacher":
            raise HTTPException(status_code=403, detail="Unauthorized access. Only teachers can access this resource.")
        

        # Convert the exam_id string to an ObjectId
        #class_object_id = ObjectId(class_id)

        exams = await exam_questions_collection.find({"class_id": class_id}, {"_id": 1}).to_list(length=None)
        
        # Extract the exam IDs from the results
        exam_ids = [str(exam["_id"]) for exam in exams]

        # Return the list of exam IDs
        return {"exam_ids": exam_ids}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


#get one exam id 
@router.get("/get_one_exam_id")
async def get_exam_by_id(exam_id: str) -> Dict:
    try:
        # Convert the exam_id string to an ObjectId
        exam_object_id = ObjectId(exam_id)
        
        # Query the database to find the exam by its ObjectId
        exam = await exam_questions_collection.find_one({"_id": exam_object_id})
        
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Convert ObjectId fields to strings
        exam = convert_object_id(exam)
        
        # Return the exam document
        return {"exam_question": exam}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
