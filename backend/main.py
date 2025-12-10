from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from dotenv import load_dotenv
from datetime import datetime
import sys
import os

# Load environment variables
load_dotenv()

from .database import engine, Base, get_db
from . import models, schemas
from .services import linkedin, agent, email

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Job Search Agent")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Job Search Agent API is running"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/{email}", response_model=schemas.User)
def get_user(email: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/jobs/search", response_model=List[schemas.Job])
def search_jobs(query: str, location: str = "remote", db: Session = Depends(get_db)):
    # 1. Fetch from RapidAPI (or Mock)
    try:
        rapid_jobs = linkedin.search_jobs(query, location)
    except Exception as e:
        print(f"ERROR in search_jobs (fetching): {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

    # 2. Store/Update in DB (Optional, but good for caching/referencing)
    jobs_to_return = []
    try:
        for r_job in rapid_jobs:
            # Check if exists
            db_job = db.query(models.Job).filter(models.Job.rapidapi_id == r_job['job_id']).first()
            if not db_job:
                db_job = models.Job(
                    rapidapi_id=r_job['job_id'],
                    title=r_job['job_title'],
                    company=r_job['company_name'],
                    location=r_job['location'],
                    description=r_job['job_description'],
                    hr_email=r_job.get('hr_email'), # Save HR email
                    url=r_job['linkedin_job_url_cleaned'],
                    posted_at=datetime.utcnow() # Add if model supports it
                )
                db.add(db_job)
                db.commit()
                db.refresh(db_job)
            jobs_to_return.append(db_job)
    except Exception as e:
        print(f"ERROR in search_jobs (db saving): {e}")
        raise HTTPException(status_code=500, detail=f"Error saving jobs: {str(e)}")
    
    return jobs_to_return

@app.post("/apply/", response_model=schemas.Application)
def apply_for_job(application: schemas.ApplicationCreate, user_id: int, db: Session = Depends(get_db)):
    # 1. Get User and Job
    user = db.query(models.User).filter(models.User.id == user_id).first()
    job = db.query(models.Job).filter(models.Job.id == application.job_id).first()
    
    if not user or not job:
        raise HTTPException(status_code=404, detail="User or Job not found")

    # 2. Check for HR Email
    if job.hr_email:
        # Generate Email Content via Agent
        user_details = {
            "name": user.name,
            "email": user.email,
            "phone_number": user.phone_number,
            "skills": user.skills,
            "experience": user.experience
        }
        job_details = {
            "title": job.title,
            "company": job.company,
            "description": job.description
        }
        
        email_content = agent.generate_email_content(user_details, job_details)
        
        # Send Email
        email_sent = email.send_email(job.hr_email, f"Application for {job.title}", email_content, attachment_path=user.resume_path)
        status = "email_sent" if email_sent else "failed"
    else:
        # Handle cases where no HR email is found
        email_content = f"No HR email found. Please apply manually at {job.url}"
        status = "manual_apply_required"

    # 4. Create Application Record
    new_application = models.Application(
        user_id=user.id,
        job_id=job.id,
        status=status,
        generated_email_content=email_content
    )
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    
    return new_application

@app.get("/applications/{user_id}", response_model=List[schemas.Application])
def get_applications(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Application).filter(models.Application.user_id == user_id).all()
