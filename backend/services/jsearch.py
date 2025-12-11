import requests
import os
from typing import List, Dict
from .utils import extract_email

# Credentials
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"


def search_jobs(filters: Dict) -> List[Dict]:
    """
    Search for jobs using JSearch RapidAPI.
    """
    url = f"https://{RAPIDAPI_HOST}/search"
    
    # Construct "query" parameter from title and location
    title = filters.get("title_filter", "")
    location = filters.get("location_filter", "")
    query_val = f"{title} in {location}".strip()
    if not query_val.strip(" in"): # If both empty
        query_val = "Software Engineer" # Fallback

    # Base params
    querystring = {
        "query": query_val,
        "page": "1",
        "num_pages": "1",
        "country": "us" # Default, could extract from location if sophisticated, but agent can pass jsearch_country if needed.
    }

    # Map filters
    
    # Remote
    if filters.get("remote") == "true":
        querystring["work_from_home"] = "true"

    # Date Posted (all, today, 3days, week, month)
    # Map from jsearch_date_posted provided by agent
    if filters.get("jsearch_date_posted"):
        querystring["date_posted"] = filters.get("jsearch_date_posted")
    
    # Job Requirements (experience etc)
    if filters.get("jsearch_job_requirements"):
        querystring["job_requirements"] = filters.get("jsearch_job_requirements")

    # Employment Types (FULLTIME, CONTRACTOR, PARTTIME, INTERN)
    # Map from type_filter or ai_employment_type_filter
    job_type = filters.get("type_filter") or filters.get("ai_employment_type_filter")
    if job_type:
        # Normalize: remove underscores, ensure valid values
        # Valid: FULLTIME, CONTRACTOR, PARTTIME, INTERN
        # User might pass FULL_TIME.
        normalized_type = job_type.replace("_", "").upper()
        if normalized_type in ["FULLTIME", "CONTRACTOR", "PARTTIME", "INTERN"]:
            querystring["employment_types"] = normalized_type
            
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    print(f"DEBUG: JSearch Params: {querystring}")

    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"DEBUG: JSearch Status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        jobs_list = data.get("data", [])
        
        normalized_jobs = []
        for item in jobs_list:
            description = item.get("job_description") or ""
            hr_email = extract_email(description)

            # JSearch returns rich data, map carefully
            job_obj = {
                "job_id": str(item.get("job_id")),
                "job_title": item.get("job_title"),
                "company_name": item.get("employer_name"),
                "location": item.get("job_location") or f"{item.get('job_city')}, {item.get('job_country')}",
                "description": description or "No description",
                "job_description": description or "No description",
                "hr_email": hr_email,
                "url": item.get("job_apply_link") or item.get("job_google_link") or "#",
                "linkedin_job_url_cleaned": item.get("job_apply_link") or "#",
                "posted_at": item.get("job_posted_at_datetime_utc")
            }
            
            if job_obj["job_title"]:
                 normalized_jobs.append(job_obj)
                 
        print(f"DEBUG: JSearch found {len(normalized_jobs)} jobs")
        return normalized_jobs

    except Exception as e:
        print(f"ERROR in jsearch.search_jobs: {e}")
        return []
