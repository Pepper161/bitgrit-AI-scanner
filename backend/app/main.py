from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import tempfile
import PyPDF2
import docx2txt
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Resume Screening API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class QuestionsResponse(BaseModel):
    questions: List[str]

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    text = ""
    with open(file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    return docx2txt.process(file_path)

def extract_text_from_resume(file_path):
    """Extract text from a resume file based on its extension."""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_extension == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

def generate_questions(resume_text):
    """Generate questions based on resume text using OpenAI."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant that helps recruiters by generating relevant interview questions based on a candidate's resume. Generate 5-7 specific questions that will help assess the candidate's skills, experience, and fit for potential roles."},
                {"role": "user", "content": f"Here is the resume text:\n\n{resume_text}\n\nGenerate relevant interview questions based on this resume."}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        
        # Extract the generated questions from the response
        questions_text = response.choices[0].message.content
        
        # Split the text into individual questions
        questions = [q.strip() for q in questions_text.split("\n") if q.strip() and "?" in q]
        
        # If no questions were found, try a different approach
        if not questions:
            questions = [q.strip() for q in questions_text.split("\n") if q.strip()]
        
        return questions
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Resume Screening API is running"}

@app.post("/api/analyze-resume", response_model=QuestionsResponse)
async def analyze_resume(resume: UploadFile = File(...)):
    """
    Analyze a resume and generate relevant interview questions.
    """
    # Check file extension
    file_extension = os.path.splitext(resume.filename)[1].lower()
    if file_extension not in [".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(await resume.read())
        temp_file_path = temp_file.name
    
    try:
        # Extract text from the resume
        resume_text = extract_text_from_resume(temp_file_path)
        
        # Generate questions based on the resume text
        questions = generate_questions(resume_text)
        
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)