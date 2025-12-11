from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

from .database import engine
from . import models
from .routers import users, jobs, applications

# Create database tables
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Auto Job Apply System")


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(applications.router)


# Mount frontend directory
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
