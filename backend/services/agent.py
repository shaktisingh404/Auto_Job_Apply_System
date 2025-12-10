import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

def generate_email_content(user_details: dict, job_details: dict) -> str:
    """
    Generate a cold email using Google Gemini.
    """
    
    prompt = f"""
    You are an expert career coach and copywriter. Write a professional and compelling cold email for a job application.
    
    Candidate Details:
    Name: {user_details.get('name')}
    Email: {user_details.get('email')}
    Phone: {user_details.get('phone_number')}
    Skills: {user_details.get('skills')}
    Experience: {user_details.get('experience')}
    
    Job Details:
    Title: {job_details.get('title')}
    Company: {job_details.get('company')}
    Description: {job_details.get('description')}
    
    The email should be concise, highlight relevant skills, and ask for an interview.
    IMPORTANT: Mention that the candidate's resume is attached to this email.
    """

    # Mock response if key is not set
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Using Mock Data for Gemini Agent (Key not found)")
        return f"""Subject: Application for {job_details.get('title')} at {job_details.get('company')}

Dear Hiring Manager,

I am writing to express my strong interest in the {job_details.get('title')} position at {job_details.get('company')}. With my background in {user_details.get('skills')}, I am confident in my ability to contribute effectively to your team.

{user_details.get('experience')}

I would welcome the opportunity to discuss how my skills align with your needs. Thank you for your time and consideration.

Best regards,
{user_details.get('name')}
"""

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        # Fallback to Mock Data so the app doesn't break
        return f"""Subject: Application for {job_details.get('title')} at {job_details.get('company')} (Fallback)

Dear Hiring Manager,

I am writing to express my strong interest in the {job_details.get('title')} position at {job_details.get('company')}. With my background in {user_details.get('skills')}, I am confident in my ability to contribute effectively to your team.

{user_details.get('experience')}

I would welcome the opportunity to discuss how my skills align with your needs. Thank you for your time and consideration.

Best regards,
{user_details.get('name')}
"""
