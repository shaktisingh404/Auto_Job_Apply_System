import requests
import os
import re
from typing import List, Dict

# Specific credentials for Active Jobs DB
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "8b25aa6a19msh5f1231629a205a7p16e368jsn458fa3565a76")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST_ACTIVE_JOBS_DB", "active-jobs-db.p.rapidapi.com")

def extract_email(text: str) -> str:
    """Extracts the first email address found in the text."""
    if not text:
        return None
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

def search_jobs(filters: Dict) -> List[Dict]:
    """
    Search for jobs using Active Jobs DB RapidAPI.
    """
    url = f"https://{RAPIDAPI_HOST}/active-ats-24h"
    
    # Defaults
    querystring = {
        "limit": "10",
        "offset": "0",
        "description_type": "text"
    }

    # Map generic filters to API specific ones if needed
    # The agent provides: title_filter, location_filter, which match exactly.
    if filters:
        querystring.update(filters)
        
        # Ensure correct type for API (sometimes APIs are picky about boolean strings)
        if querystring.get("remote") == "true":
             pass # valid
        elif querystring.get("remote") == True:
             querystring["remote"] = "true"

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    print(f"DEBUG: Active Jobs DB Params: {querystring}")

    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"DEBUG: Active Jobs DB Status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        # active-jobs-db active-ats-7d returns a list directly or data object?
        # Based on user input example "active-ats-7d", usually returns list or paginated.
        # Let's assume list or key 'data' similar to others. 
        # Actually user didn't show response format, assuming standard list or single key.
        # Safe approach: check type.
        
        jobs_list = data if isinstance(data, list) else data.get('data', [])
        
        normalized_jobs = []
        for item in jobs_list:
            description = item.get("description") or item.get("job_description") or ""
            hr_email = extract_email(description)

            job_obj = {
                "job_id": str(item.get("id") or item.get("job_id") or ""),
                "job_title": item.get("title") or item.get("job_title") or "",
                "company_name": item.get("company_name") or item.get("organization") or "",
                "location": item.get("location") or "",
                "description": description or "No description",
                "job_description": description or "No description", # Alias for main.py compatibility
                "hr_email": hr_email,
                "url": item.get("url") or "#",
                "linkedin_job_url_cleaned": item.get("url") or "#", # Alias for main.py compatibility
                "posted_at": item.get("date_posted") or item.get("posted_date")
            }
            # Only add if minimal info is present
            if job_obj["job_title"] and job_obj["company_name"]:
                 normalized_jobs.append(job_obj)
                 
        print(f"DEBUG: Active Jobs DB found {len(normalized_jobs)} jobs")
        return normalized_jobs

    except Exception as e:
        print(f"ERROR in active_jobs.search_jobs: {e}")
        return []
