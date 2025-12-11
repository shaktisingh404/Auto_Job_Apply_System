from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .. import models, schemas
from ..database import get_db
from ..services import linkedin, job_filter_agent, active_jobs, jsearch

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.get("/search", response_model=List[schemas.Job])
def search_jobs(query: str = "", location: str = "remote", user_id: Optional[int] = None, db: Session = Depends(get_db)):
    
    filters = {}
    
    if user_id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user_details = {
                "skills": user.skills,
                "experience": user.experience,
                "location": user.location
            }
            filters = job_filter_agent.generate_search_filters(user_details, query)


    if not filters:
        if not query:
            filters = {"title_filter": "Software Engineer"}
        else:
            filters = {"title_filter": query}
    
    if location and "location_filter" not in filters:
         filters["location_filter"] = location

    rapid_jobs = []
    try:
        rapid_jobs = linkedin.search_jobs(filters)
    except Exception as e:
        pass
        
    active_db_jobs = []
    try:
        active_db_jobs = active_jobs.search_jobs(filters)
    except Exception as e:
        pass

    jsearch_jobs = []
    try:
        jsearch_jobs = jsearch.search_jobs(filters)
    except Exception as e:
        pass

    all_fetched_jobs = rapid_jobs + active_db_jobs + jsearch_jobs
    
    if not all_fetched_jobs:
         # Only raise if BOTH failed or returned nothing
         pass


    jobs_to_return = []
    
    applied_job_ids = set()
    if user_id:
        applied_jobs = db.query(models.Application).filter(
            models.Application.user_id == user_id,
            models.Application.status == "email_sent"
        ).all()
        applied_job_ids = {app.job_id for app in applied_jobs}

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
                    hr_email=r_job.get('hr_email'),
                    url=r_job['linkedin_job_url_cleaned'],
                    posted_at=datetime.utcnow()
                )
                db.add(db_job)
                db.commit()
                db.refresh(db_job)
            
            if db_job.id in applied_job_ids:
                continue

            jobs_to_return.append(db_job)
    except Exception as e:

        raise HTTPException(status_code=500, detail=f"Error saving jobs: {str(e)}")
    
    return jobs_to_return
