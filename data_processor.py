import os
from google import genai
from google.genai import types
import json

def get_gemini_match(nursery_name, candidates):
    """
    Use Gemini to find the best match for a nursery name from a list of candidates.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Find the best match for the nursery name '{nursery_name}' from the following list.
    If no reasonable match exists, return null.
    
    Candidates:
    {json.dumps(candidates, ensure_ascii=False)}
    
    Return ONLY a JSON object: {{"match": "candidate_name_or_null"}}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        result = json.loads(response.text)
        return result.get("match")
    except:
        return None

def merge_data(nursery_records, bed_records):
    """
    Merge Bed Data into Nursery Data based on ID or Name.
    """
    merged = []
    
    # Build Bed Lookup Dict
    # Key: Nursery Name (from field "保育園"), Value: Record
    bed_by_name = {}
    for r in bed_records:
        b_name = r.get("保育園", {}).get("value", "")
        if b_name:
            bed_by_name[b_name] = r
    # bed_by_id = {r.get("施設ID", {}).get("value", ""): r for r in bed_records} # If ID exists
    
    for nursery in nursery_records:
        # Changed "施設名" to "name" based on App 218 definition
        n_name = nursery.get("name", {}).get("value", "")
        # client_name = nursery.get("client_name", {}).get("value", "")
        
        # 1. Exact Name Match
        match = bed_by_name.get(n_name)
        
        # 2. Fuzzy Match (Gemini) - Optional pass if critical
        # if not match and n_name:
        #    matched_name = get_gemini_match(n_name, list(bed_by_name.keys())[:50]) # Limit candidates
        #    if matched_name:
        #        match = bed_by_name.get(matched_name)
        
        merged_item = {
            "master": nursery,
            "bed": match if match else None,
            "status": "matched" if match else "unmatched"
        }
        merged.append(merged_item)
        
    return merged
