from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Any
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    skills: str
    experience: str
    phone_number: Optional[str] = None
    location: Optional[str] = None
    resume_path: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Job Schemas
class JobBase(BaseModel):
    rapidapi_id: str
    title: Optional[str] = ""
    company: Optional[str] = ""
    location: Optional[str] = ""
    description: Optional[str] = "No description"
    hr_email: Optional[str] = None 
    url: Optional[str] = "#"

    @field_validator('title', 'company', 'location', 'description', 'url', mode='before')
    @classmethod
    def set_defaults(cls, v: Any) -> str:
        # If value is None, return appropriate default based on field? 
        # Actually field_validator runs per field.
        # But we can just return empty string or specific default if None
        if v is None:
            return "" # Or let the default= take over? 
            # Wait, mode='before' receives None. If we return None, default might NOT trigger if Optional allows None.
            # We want to force a string.
            return ""
        return str(v)

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: int
    posted_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Application Schemas
class ApplicationBase(BaseModel):
    job_id: int

class ApplicationCreate(ApplicationBase):
    pass

class Application(ApplicationBase):
    id: int
    user_id: int
    status: str
    generated_email_content: Optional[str] = None
    applied_at: datetime
    job: Job

    class Config:
        orm_mode = True
