import requests
import json

def main(event):
    api_key = "PRIVATE_APP_TOKEN"  
        # replace with >> os.getenv('YOUR_PRIVATE_APP_SECRET_HERE')
        # ensure the private app has read/write authority for the objects you are operating, keeping in mind that engagements are under the contacts object
    main_object = "company"  
        # this will be the object you are STARTING from
        # example, you want to see all meetings for a certain company, this would be 'company'
    main_object_id = event.get('object').get('objectId')  

    target_object = "meetings"
        # replace with >> object you want to get associated records to
        # example, you want to see all meetings for a certain company, this would be 'meetings'
    properties = [
        "hs_createdate",
        "hs_meeting_title",
        "hs_created_by_user_id"
    ]

    def search_target_object(api_key, main_object, main_object_id, target_object, properties):
        request_url = f"https://api.hubapi.com/crm/v3/objects/{target_object}/search"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "filterGroups": [
                {
                    "filters": [
                        {
                            "value": main_object_id,
                            "propertyName": f"associations.{main_object}",
                            "operator": "EQ"
                        }
                    ]
                }
            ],
            "sorts": [
                {
                    "propertyName": "hs_createdate",
                    "direction": "DESCENDING"
                }
            ],
            "properties": properties,
            "limit": 1
        })
        print(payload)
        response = requests.post(request_url, headers=headers, data=payload)
        if response.status_code == 200:
            data = response.json()
            if data['total'] > 0:
                return data['results'][0]
        else:
            print(f"Failed to search {target_object}: {response.status_code}")
        return None

    def owner_lookup(api_key, owner_id):
        url = f"https://api.hubapi.com/crm/v3/owners/{owner_id}?idProperty=userid&archived=false"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        response = requests.get(url, headers=headers)
        print(response.json())
        if response.status_code == 200:
            data = response.json()
            return data['id']
        else:
            print(f"Failed to lookup owner: {response.status_code}")
        return None

    def update_main_object(api_key, main_object, object_id, owner_id):
        url = f"https://api.hubapi.com/crm/v3/objects/{main_object}/{object_id}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        payload = json.dumps({
            "properties": {
                "hubspot_owner_id": owner_id
            }
        })
        response = requests.patch(url, headers=headers, data=payload)
        if response.status_code == 200:
            print(f"Successfully updated {main_object} {object_id}")
        else:
            print(f"Failed to update {main_object}: {response.status_code}")

    # Search for a meeting associated with the main object
    recent_target_object = search_target_object(api_key, main_object, main_object_id, target_object, properties)

    if recent_target_object:
        # Meeting found, proceed with owner lookup and update the main object
        print(recent_target_object)
        owner_id = recent_target_object['properties']['hs_created_by_user_id']
        owner_id = owner_lookup(api_key, owner_id)
        if owner_id:
            update_main_object(api_key, main_object, main_object_id, owner_id)
    else:
        print(f"No associated {target_object} found for the main object.")
