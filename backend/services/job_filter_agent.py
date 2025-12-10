import os
import json
import google.generativeai as genai
from typing import Dict

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_search_filters(user_details: Dict, user_query: str) -> Dict:
    """
    Generates RapidAPI LinkedIn Job Search filters using Google Gemini based on user profile and query.
    """
    
    if not GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not set. Using default filters.")
        return {"title_filter": user_query}

    prompt = f"""
    You are an expert search query optimizer for a Job Search API.
    Your goal is to translate a user's natural language search query and their professional profile into a precise set of API filters.

    **USER PROFILE:**
    * Skills: {user_details.get('skills', '')}
    * Experience: {user_details.get('experience', '')}
    * Preferred Location: {user_details.get('location', 'Not specified')}
    
    **USER QUERY:** "{user_query}"

    **AVAILABLE API FILTERS (Unified LinkedIn, Active Jobs, JSearch):**
    - title_filter: String (Job title)
    - location_filter: String (Support OR)
    - description_filter: String (Keywords)
    - remote: "true"
    - date_filter: String (YYYY-MM-DD)
    - type_filter: String (CONTRACTOR, FULL_TIME, INTERN, OTHER, PART_TIME, TEMPORARY, VOLUNTEER)
    - jsearch_date_posted: String (all, today, 3days, week, month)
    - jsearch_job_requirements: String (under_3_years_experience, more_than_3_years_experience, no_experience, no_degree)

    **INSTRUCTIONS:**
    1. **LOCATION LOGIC (CRITICAL):**
       - Check if the **USER QUERY** explicitly mentions a city or country (e.g., "in London"). If YES, use that as 'location_filter'.
       - If NO specific location in query, you **MUST** use the "Preferred Location" from the **USER PROFILE** as the 'location_filter'.
       - Do NOT leave 'location_filter' empty unless both Query and Profile have no location.
    2. **TITLE LOGIC:**
       - If USER QUERY is provided, extract job title.
       - **IF USER QUERY IS EMPTY:** Infer the most likely Job Title from Skills and Experience.
    3. Use User Skills to populate 'description_filter' to ensure relevance.
    4. **REMOTE LOGIC:** If user asks for "remote", set "remote": "true".
    5. **JOB TYPE LOGIC:** Map query terms to 'type_filter' (CONTRACTOR, INTERN). Use uppercase.
    6. **EXPERIENCE LOGIC:**
       - Map User Experience to 'jsearch_job_requirements':
         - 0-3 years -> "under_3_years_experience"
         - 3+ years -> "more_than_3_years_experience"
         - Entry/Intern -> "no_experience"
    7. **DATE LOGIC:** Map user timeframe (e.g. "recent", "today") to 'jsearch_date_posted' (today, 3days, week, month).
    8. Return ONLY a valid JSON object.
    
    **EXAMPLE OUTPUT:**
    {{
        "title_filter": "Python Developer",
        "description_filter": "FastAPI, AWS",
        "location_filter": "United States",
        "type_filter": "FULL_TIME",
        "jsearch_job_requirements": "more_than_3_years_experience",
        "jsearch_date_posted": "week"
    }}
    """

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Clean response text to ensure valid JSON (remove backticks if any)
        text_response = response.text.strip()
        if text_response.startswith("```"):
            text_response = text_response.strip("`")
            if text_response.startswith("json"):
                text_response = text_response[4:]
        
        filters = json.loads(text_response)
        return filters

    except Exception as e:
        print(f"Error generating search filters: {e}")
        # Fallback to basic search if AI fails
        return {"title_filter": user_query}
