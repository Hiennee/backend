from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import json
from typing import Dict, Any
import logging
import sys
from dotenv import load_dotenv

# Update imports to use absolute imports from app root
from aimodel.modules.document_extraction.extractor import extract_resume
from aimodel.modules.scoring.scorer import calculate_total_score
from aimodel.modules.summarization.summarizer import summarize_resume
from aimodel.modules.summarization.evaluator import evaluate_resume
from aimodel.modules.scoring.education import calculate_education_score
from aimodel.modules.scoring.experience import calculate_experience_score
from aimodel.modules.scoring.projects import calculate_projects_score
from aimodel.modules.scoring.awards import calculate_awards_score
from aimodel.modules.scoring.certifications import calculate_certifications_score

# Load environment variables
load_dotenv()

async def evaluate_cv_endpoint(file: UploadFile = File(...)) -> dict:
    temp_file = None
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise ValueError("Only PDF files supported")

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()  # Close file before processing

        # Process CV
        resume = extract_resume(temp_file.name)
        scoring_result = calculate_total_score(resume)

        return {
            "success": True,
            "cv_data": resume.dict(),
            "scores": scoring_result,
            "status": "Pass" if scoring_result["total_score"] >= 70 else "Fail"
        }
    
    except Exception as e:
        return {
            "success": False,
            "detail": str(e)
        }
    
    finally:
        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Error deleting temp file: {str(e)}")


# Keep existing utility functions
def get_cv_json_data(file_path: str) -> Dict[str, Any]:
    """Extract structured JSON data from a CV file."""
    try:
        resume = extract_resume(file_path)
        return resume.dict()
    except Exception as e:
        print(f"Error extracting CV data: {e}")
        return {}

def evaluate_cv(file_path: str) -> Dict[str, Any]:
    """Evaluate a CV and provide detailed evaluation information."""
    try:
        resume = extract_resume(file_path)
        scoring_result = calculate_total_score(resume)
        summary = summarize_resume(resume)
        evaluation = evaluate_resume(resume)
        
        return {
            "cv_data": resume.dict(),
            "scores": {
                "education": calculate_education_score(resume.education),
                "experience": calculate_experience_score(resume.professional_experience),
                "projects": calculate_projects_score(resume.projects),
                "awards": calculate_awards_score(resume.awards),
                "certifications": calculate_certifications_score(resume.certifications),
                "total_score": scoring_result["total_score"],
                "status": scoring_result["status"]
            },
            "ai_summarization": summary,
            "ai_evaluation": evaluation
        }
    except Exception as e:
        print(f"Error evaluating CV: {e}")
        return {}

def export_to_json(data: Dict[str, Any], output_file: str) -> None:
    """Export evaluation data to a JSON file."""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # print(f"Evaluation data exported to {output_file}")
    except Exception as e:
        print(f"Error exporting to JSON: {e}")