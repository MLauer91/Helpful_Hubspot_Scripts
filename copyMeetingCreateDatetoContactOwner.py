import requests
import json
from datetime import datetime

api_key = "YOUR_API_KEY_HERE"  
    # replace with >> os.getenv('YOUR_PRIVATE_APP_SECRET_HERE')
    # ensure the private app has read/write authority for the objects you are operating, keeping in mind that engagements are under the contacts object
main_object = "contacts" 
    # this will be the object you are STARTING from
    # example, you want to see all meetings for a certain contact, this would be 'contacts'
main_object_id = "1234567890"  
    # replace with >> event["inputFields"]["contactid"] 
    # ensure you have the property to include in code as 'main_object_id' for the 'Record ID' of the record in the workflow
target_object = "meetings"
    # replace with >> object you want to get associated records to
    # example, you want to see all meetings for a certain contact, this would be 'meetings'
record_type = "meetings"
    # this isn't critical to run but if you want to label these records with a custom label, change this to identiy the call
properties = {
    "hs_createdate": "date",
    "hs_meeting_title": "regular",
    "hs_created_by_user_id": "regular"
}
    # properties are under two types, "date" and "regular"
    # date will format the date into a standard "MM-DD-YYYY" format
    # regular will treat the value as a string

today = datetime.today().strftime("%m-%d-%Y")

# This is the function which gets the related records to your main object
# Example, this will call for all the meetings related to a specific contact
def get_object_details(api_key, main_object, main_object_id, target_object, record_type, properties):
    def get_associated_ids(main_object, main_object_id, target_object, api_key):
        url = f"https://api.hubapi.com/crm/v3/objects/{main_object}/{main_object_id}/associations/{target_object}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            relevant_ids = [assoc['id'] for assoc in response.json().get('results', [])]
            return relevant_ids
        else:
            print(f"Failed to fetch associated ids: {response.status_code}")
            return None

    def parse_date(date_str):
        try:
            return datetime.fromisoformat(date_str.rstrip("Z")).strftime("%m-%d-%Y")
        except:
            return None

    record_ids = get_associated_ids(main_object, main_object_id, target_object, api_key)
    if record_ids is None:
        return []

    url = f"https://api.hubapi.com/crm/v3/objects/{target_object}/batch/read"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = json.dumps({
        "inputs": [{"id": record_id} for record_id in record_ids],
        "properties": list(properties.keys())
    })

    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        data = response.json()
        results = []
        for item in data.get('results', []):
            record_id = item.get('id')
            result = {'record_id': record_id, 'record_type': record_type}
            for prop, prop_type in properties.items():
                value = item.get('properties', {}).get(prop, None)
                if prop_type == 'date':
                    value = parse_date(value)
                result[prop] = value
            results.append(result)
        return results
    else:
        print(f"Failed to fetch object details: {response.status_code}, Message: {response.text}")
        return []

# This will call Hubspot to get the id required to change the owner of the target object based on who created the meeting
def owner_lookup(api_key, owner_id):
    url = f"https://api.hubapi.com/crm/v3/owners/{owner_id}?idProperty=userid&archived=false"

    payload = {}
    headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {api_key}'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json()
    #print(data['id'])
    return data['id']

# This will update the specified contact with the correct owner ID from the owner lookup function
def update_contact(api_key, contact_id, owner_id):
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"

    payload = json.dumps({
    "properties": {
        "hubspot_owner_id": f"{owner_id}"
    }
    })
    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {api_key}'
    }

    response = requests.request("PATCH", url, headers=headers, data=payload)

    return response.text

# This is the series of functions which will parse through all engagements on a contact, find the one created today, and update the owner property
engagements_results = get_object_details(api_key, main_object, main_object_id, target_object, record_type, properties)

# This is the for loop for going through each engagement / meeting record on the contact
for meeting in engagements_results:
    # This if statement only activates if the create date on the record matches today's date, assuming this is paired up with proper enrollment criteria
    if today == meeting['hs_createdate']:
        print(meeting['hs_created_by_user_id'])
        owner_id = owner_lookup(api_key, owner_id=meeting['hs_created_by_user_id'])
        print(owner_id)
        print(update_contact(api_key, contact_id=main_object_id, owner_id=owner_id))
        break
