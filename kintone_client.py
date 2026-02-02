import requests
import os

# Kintone Constants
SUBDOMAIN = "n2amf" # From user URL: https://n2amf.cybozu.com/...
NURSERY_APP_ID = 218
BED_APP_ID = 32

def fetch_all_records(app_id, api_token, base_query=""):
    """
    Fetch all records using ID-based pagination to bypass 10k offset limit.
    """
    url = f"https://{SUBDOMAIN}.cybozu.com/k/v1/records.json"
    headers = {"X-Cybozu-API-Token": api_token}
    records = []
    limit = 500
    last_id = 0
    
    while True:
        # Construct query: (Original Condition) and $id > last_id order by $id asc
        if base_query:
            query = f"({base_query}) and $id > {last_id} order by $id asc limit {limit}"
        else:
            query = f"$id > {last_id} order by $id asc limit {limit}"
            
        params = {
            "app": app_id,
            "query": query,
            "fields": [
                "$id", "status", "name", "client_name", "capacity", "open_date", 
                "addr_area", "addr_city", "保育園", "病床数合計_0",
                "sick_child_care", "sc_flg", "night_care", "ekbn2", "ekbn4"
            ] 
            # Ideally fetch all fields, but Kintone might error if too many.
            # To be safe, let's NOT specify fields and get all, unless payload is too huge.
            # The error 'offset' implies payload size wasn't the issue, just count.
            # Let's try fetching ALL fields first.
        }
        
        # If we don't specify fields, we get all.
        del params["fields"]

        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise Exception(f"Kintone API Error ({app_id}): {resp.text}")
            
        data = resp.json()
        rec_batch = data.get("records", [])
        
        if not rec_batch:
            break
            
        records.extend(rec_batch)
        last_id = rec_batch[-1]["$id"]["value"]
        
        if len(rec_batch) < limit:
            break
        
    return records

def get_nursery_data(api_token):
    # Filter: Status (開園状態 -> status) in "開園", "開園予定"
    query = 'status in ("開園", "開園予定")'
    return fetch_all_records(NURSERY_APP_ID, api_token, query)

def get_bed_data(api_token):
    # Fetch all for matching
    return fetch_all_records(BED_APP_ID, api_token)
