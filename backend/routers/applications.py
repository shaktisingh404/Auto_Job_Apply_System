from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..services import email_agent, email

router = APIRouter(
    tags=["applications"]
)

@router.post("/apply/", response_model=schemas.Application)
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
            "experience": user.experience,
            "linkedin_url": user.linkedin_url
        }
        job_details = {
            "title": job.title,
            "company": job.company,
            "description": job.description
        }
        
        email_content = email_agent.generate_email_content(user_details, job_details)
        
        # Send Email
        
        email_sent = email.send_email(job.hr_email, f"Application for {job.title}", email_content, attachment_path=None)
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

@router.get("/applications/{user_id}", response_model=List[schemas.Application])
def get_applications(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Application).filter(models.Application.user_id == user_id).all()
