from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    skills = Column(Text)  # Comma separated or JSON
    experience = Column(Text)
    phone_number = Column(String, nullable=True)
    location = Column(String, nullable=True) # User's preferred location
    resume_path = Column(String, nullable=True) # URL or File Path
    resume_url = Column(String, nullable=True) # Keeping for backward compatibility if needed, or replace
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    applications = relationship("Application", back_populates="user")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    rapidapi_id = Column(String, unique=True, index=True)
    title = Column(String)
    company = Column(String, default="")
    location = Column(String)
    description = Column(Text)
    hr_email = Column(String, nullable=True) # New field
    url = Column(String)
    posted_at = Column(DateTime(timezone=True), nullable=True)

    applications = relationship("Application", back_populates="job")

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    status = Column(String, default="applied") # applied, email_sent, etc.
    generated_email_content = Column(Text)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
