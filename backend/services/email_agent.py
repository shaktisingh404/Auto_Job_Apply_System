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
Write a natural, human-sounding cold email for a job application. It should feel personal,
thoughtful, and written by a real person — not an AI or a template.

Here is the candidate's information:
- Name: {user_details.get('name')}
- Skills: {user_details.get('skills')}
- Experience Summary: {user_details.get('experience')}

Job details:
- Role: {job_details.get('title')}
- Company: {job_details.get('company')}
- Description Highlights: {job_details.get('description')}

**Guidelines:**
- Do NOT include a subject line. Only write the email body.
- Start by expressing sincere interest in the role and {job_details.get('company')}.
- Keep the tone warm, respectful, and professional — avoid clichés, buzzwords, or overly polished AI-like language.
- Connect the candidate’s real experience to the expectations of the role in a natural way.
- Use short, readable paragraphs that feel conversational but still professional.
- Mention that the resume is attached.
- End by politely asking if they'd be open to a brief conversation.

Return only the email body. Do not include a subject or any additional explanations.
"""

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash') 
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        # Log the error for debugging, but raise it so the application knows the email failed.
        print(f"Critical Error in Gemini Generation: {e}")
        raise e