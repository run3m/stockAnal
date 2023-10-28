from datetime import datetime
import json
from flask import (current_app)
from requests_toolbelt.multipart.encoder import MultipartEncoder
import requests
from ..db_config import get_db
import os
import re

def generateReportAndUpload(req_search, last_message, contact_details):
    db = get_db()['myDatabase'];
    last_messages = db['last_messages']
    latest_searches = db['latest_searches']
    bearer_token = current_app.config['WHATSAPP_CONFIG']['bearer_token'];
    
    with current_app.test_client() as client:
        response = client.post('/screener/generateReport', json={"just_path": True,"constraints": re.split(r',\s*(?![^(\[]*[\)\]])', req_search['query'])})
        if response.status_code == 200:
            csv_path = response.get_json()['path']
            encoder = MultipartEncoder(
                fields={
                    'file': ('babe.csv', open(csv_path, 'rb'), 'application/vnd.ms-excel'),
                    'messaging_product': 'whatsapp',
                }
            )
            # CONTINUE HERE
            # upload the csv to whatsapp server : https://graph.facebook.com/v18.0/137217652804256/media
            media_response = requests.post("https://graph.facebook.com/v18.0/137217652804256/media", headers={'Content-Type': encoder.content_type, "Authorization": f"Bearer {bearer_token}"}, data=encoder);
            try:
                # Attempt to delete the file
                os.remove(csv_path)
                print(f"File '{csv_path}' has been deleted successfully.")
            except FileNotFoundError:
                print(f"File '{csv_path}' not found.")
            except Exception as e:
                print(f"An error occurred while deleting the file: {e}")
            
            if(media_response.status_code != 200):
                raise Exception(f"Failed to run your query. Please try again later.")
            media_id = media_response.json()["id"];
            # this will change the passed req_search. which means req_search in calling code will also change.
            req_search['media_id'] = media_id;
            
            latest_searches.update_one({"user": contact_details['wa_id']}, {"$push": {"searches": {'query' : req_search['query'], "media_id": media_id, "last_triggered" : datetime.now()}}});
            last_messages.update_one({"_id": last_message['_id']}, {"$set" : last_message})
        else:
            raise Exception(f"Failed to run your query. Please try again later.")

def sendReport(media_id, contact_details):
    bearer_token = current_app.config['WHATSAPP_CONFIG']['bearer_token'];
    if(bool(media_id)):
        media_message = json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": contact_details['wa_id'],
            "type": "document",
            "document": {
                "id" : str(media_id),
                "filename": "report.xlsx"
            }
        })
        response = requests.post("https://graph.facebook.com/v17.0/137217652804256/messages", headers={"Content-type": "application/json", "Authorization": f"Bearer {bearer_token}"}, data=media_message);
        response_data = response.json();