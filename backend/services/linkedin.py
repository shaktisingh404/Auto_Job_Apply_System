import requests
print("DEBUG: linkedin.py LOADED")
import os
import re
from typing import List, Dict
from urllib.parse import quote

# Load from environment or use defaults
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "0497530d8cmsh56f0d2763d130e5p1a652djsnf5c0fd191f89")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "linkedin-job-search-api.p.rapidapi.com")

def extract_email(text: str) -> str:
    """Extracts the first email address found in the text."""
    if not text:
        return None
    # Regex for email extraction
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

def search_jobs(filters: Dict) -> List[Dict]:
    """
    Search for jobs using RapidAPI LinkedIn Job Search API (active-jb-24h).
    """
    url = f"https://{RAPIDAPI_HOST}/active-jb-24h"
    
    # Defaults
    querystring = {
        "limit": "10",
        "offset": "0",
        "description_type": "text"
    }
    
    # Merge dynamic filters (overriding defaults if present)
    if filters:
        querystring.update(filters)

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    print("DEBUG: Inside search_jobs")
    try:
        print("DEBUG: Making request...")
        response = requests.get(url, headers=headers, params=querystring)
        print(f"DEBUG: Response status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG: Raw API Data: {data}")
        print(f"DEBUG: Key used: {RAPIDAPI_KEY[:5]}...")
        
        # The API returns a list of jobs directly or a dict with 'data'?
        # Based on typical usage of this specific API 'active-jb-24h', it usually returns a list or a paginated dict.
        # Let's handle list or dict['data'].
        
        jobs_list = data if isinstance(data, list) else data.get('data', [])
        print(f"DEBUG: jobs_list len: {len(jobs_list)}")
        
        normalized_jobs = []
        for item in jobs_list:
            # Map API fields to our internal model
            # Based on debug: 'description_text' holds the Description, 'organization' is company name
            
            description = item.get("description_text") or item.get("description") or item.get("job_description") or ""
            
            # Attempt to extract HR email
            hr_email = extract_email(description)
            
            # Location parsing
            loc_derived = item.get("locations_derived")
            location = loc_derived[0] if loc_derived and isinstance(loc_derived, list) else ""
            
            job_obj = {
                "job_id": str(item.get("id") or item.get("job_id") or ""),
                "job_title": item.get("title") or item.get("job_title") or "",
                "company_name": item.get("organization") or "",
                "location": location or "",
                "job_description": description or "No description",
                "hr_email": hr_email,
                "linkedin_job_url_cleaned": item.get("url") or item.get("linkedin_job_url_cleaned") or "#",
                "posted_date": item.get("date_posted") or item.get("posted_date")
            }
            normalized_jobs.append(job_obj)
            
        print(f"DEBUG: Returning {len(normalized_jobs)} jobs.")
        return normalized_jobs

    except Exception as e:
        print(f"DEBUG: EXCEPTION in search_jobs: {e}")
        return []
