# AI Job Application Agent

This project is an AI-powered job search and application assistant. It scrapes job listings (mocked/RapidAPI), allows users to create a profile with their resume and skills, and uses Google Gemini to generate personalized cold emails for job applications, attaching the user's resume.

## Features
- **User Profile**: Store details, skills, experience, and resume path.
- **Job Search**: Browse job listings (integrated with LinkedIn via RapidAPI, currently mocked).
- **AI Agent**: Generates professional cold emails using Google Gemini 2.5 Flash.
- **Auto-Apply**: Sends emails to HR with the generated content and attached resume.

## Setup

1.  **Clone the repository**.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Variables**:
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    RAPIDAPI_KEY=your_rapidapi_key
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    DATABASE_URL=sqlite:///./jobsearch_v3.db
    ```

## Usage

1.  **Start the Backend**:
    ```bash
    python -m uvicorn backend.main:app --reload --port 8000
    ```
2.  **Start the Frontend**:
    Serve the `frontend` folder (e.g., using Python's http.server):
    ```bash
    cd frontend
    python -m http.server 8080
    ```
3.  **Access the App**:
    Open `http://localhost:8080` in your browser.

## Project Structure
- `backend/`: FastAPI application, database models, and services (Agent, Email, LinkedIn).
- `frontend/`: HTML, CSS, and JS for the user interface.
