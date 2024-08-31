from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import exam_questions, marking, student_responses


app = FastAPI()

# CORS settings
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(exam_questions.router, prefix="/exam")
app.include_router(marking.router, prefix="/mark")
app.include_router(student_responses.router, prefix="/student")

