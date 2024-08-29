import motor.motor_asyncio
from bson import ObjectId
from app.config import MONGO_DB_URI

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DB_URI)
database = client['test']
exam_questions_collection = database['examquestions']
student_response_collection = database['studentresponse']
exam_results_collection = database['examresults']

def convert_object_id(document):
    if isinstance(document, dict):
        for key, value in document.items():
            if isinstance(value, ObjectId):
                document[key] = str(value)
            elif isinstance(value, dict):
                convert_object_id(value)
            elif isinstance(value, list):
                for item in value:
                    convert_object_id(item)
    elif isinstance(document, list):
        for item in document:
            convert_object_id(item)
    return document

# Add other MongoDB utility functions here...
