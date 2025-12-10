import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_email_content(user_details: dict, job_details: dict) -> str:
    """
    Generate a highly personalized cold email using Google Gemini.
    """
    
    # Validation to ensure we don't proceed without a key
    if not GEMINI_API_KEY:
        raise ValueError("API Key is missing. Please set GEMINI_API_KEY environment variable.")

    prompt = f"""
    You are an expert career coach and professional copywriter specializing in high-conversion cold emails.
    
    **OBJECTIVE:** Write a concise, persuasive, and professional cold email for a job application that distinguishes the candidate from the crowd.

    **CANDIDATE PROFILE:**
    * Name: {user_details.get('name')}
    * Key Skills: {user_details.get('skills')}
    * Experience Summary: {user_details.get('experience')}

    **JOB TARGET:**
    * Role: {job_details.get('title')}
    * Company: {job_details.get('company')}
    * Job Description Insights: {job_details.get('description')}

    **WRITING GUIDELINES:**
    1. **Subject Line:** Create a subject line that is professional but catchy (e.g., "Regarding [Role] / [Candidate's Top Achievement]").
    2. **The Hook:** Start by expressing genuine interest in {job_details.get('company')}.
    3. **The Bridge:** Do not just list skills. Connect the candidate's specific experience directly to the requirements found in the job description. Show *how* they can solve the company's problems.
    4. **Tone:** Confident, humble, and strictly professional. Avoid overly flowery language.
    5. **Formatting:** Use short paragraphs for readability. 
    6. **Requirement:** Explicitly mention that the resume is attached.
    7. **Call to Action:** End with a clear, low-pressure request for a brief conversation.

    **OUTPUT:** Return strictly the email content (Subject and Body). Do not include conversational filler like "Here is your email."
    """

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Switched to 1.5-flash as '2.5' is not currently a standard production endpoint.
        # You can change this to 'gemini-2.0-flash-exp' if you have access to the preview.
        model = genai.GenerativeModel('gemini-2.5-flash') 
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        # Log the error for debugging, but raise it so the application knows the email failed.
        print(f"Critical Error in Gemini Generation: {e}")
        raise e