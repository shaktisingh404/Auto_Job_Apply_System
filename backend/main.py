from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from dotenv import load_dotenv
from datetime import datetime
import sys
import os

# Load environment variables
load_dotenv()

from .database import engine, Base, get_db
from . import models, schemas
from .services import linkedin, email_agent, email, job_filter_agent, active_jobs, jsearch

from fastapi.staticfiles import StaticFiles

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



@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        new_user = models.User(**user.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        print(f"CRITICAL ERROR in create_user: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/users/{email}", response_model=schemas.User)
def get_user(email: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/jobs/search", response_model=List[schemas.Job])
def search_jobs(query: str = "", location: str = "remote", user_id: Optional[int] = None, db: Session = Depends(get_db)):
    
    filters = {}
    
    # Use Agent if user_id is provided
    if user_id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user_details = {
                "skills": user.skills,
                "experience": user.experience,
                "location": user.location
            }
            # Generate filters using Gemini
            filters = job_filter_agent.generate_search_filters(user_details, query)
            print(f"DEBUG: Agent generated filters: {filters}")

    # Fallback / Merge provided location
    if not filters:
        # If no filters and no query, default to something generic or fail gracefully
        if not query:
             # Try to search for "Software Engineer" if nothing else, or handle as error?
             # Better: let the API handle empty title filter if possible, or use a default.
             filters = {"title_filter": "Software Engineer"} # Default fallback
        else:
            filters = {"title_filter": query}
    
    # Ensure location from input is used if not handled/overridden smartly by agent (or to enforce it)
    if location and "location_filter" not in filters:
         filters["location_filter"] = location

    # 1. Fetch from RapidAPI (LinkedIn)
    rapid_jobs = []
    try:
        rapid_jobs = linkedin.search_jobs(filters)
    except Exception as e:
        print(f"ERROR in search_jobs (LinkedIn fetching): {e}")
        # Don't raise, just log, so we can try the other source
        
    # 2. Fetch from Active Jobs DB (Indeed/Naukri)
    active_db_jobs = []
    try:
        active_db_jobs = active_jobs.search_jobs(filters)
    except Exception as e:
        print(f"ERROR in search_jobs (Active Jobs DB fetching): {e}")

    # 3. Fetch from JSearch (RapidAPI)
    jsearch_jobs = []
    try:
        jsearch_jobs = jsearch.search_jobs(filters)
    except Exception as e:
        print(f"ERROR in search_jobs (JSearch fetching): {e}")

    # Combine results
    all_fetched_jobs = rapid_jobs + active_db_jobs + jsearch_jobs
    
    if not all_fetched_jobs:
         # Only raise if BOTH failed or returned nothing
         print("WARNING: No jobs found from any source.")
         # return [] # Or raise 404? Let's return empty list.


    # 2. Store/Update in DB (Optional, but good for caching/referencing)
    jobs_to_return = []
    try:
        for r_job in all_fetched_jobs:
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
        
        email_content = email_agent.generate_email_content(user_details, job_details)
        
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

# Mount frontend directory
import os
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
