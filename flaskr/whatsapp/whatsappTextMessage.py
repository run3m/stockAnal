from datetime import datetime
import json
import os
import random
import re

import requests
from flask import (current_app)
from ..db_config import get_db

def handle_message(message_details, contact_details):
    print(f"Smash message type text");
    db = get_db()['myDatabase'];
    interactive_obj = None;
    message = str(message_details['text']['body']);
    last_messages = db['last_messages']
    latest_searches = db['latest_searches']
    last_message = last_messages.find_one({"user": contact_details['wa_id']});
    print(f"Smash last message: {last_message}")
    if(message.strip().lower() == 'hi' or message.strip().lower() == 'hello'):
        #start convo
        print("Smash, a")
        interactive_obj = start_convo(contact_details);
    elif(re.search(r'[><=\[\]]', message) != None):
        # give report
        print("Smash, b")
    elif(bool(last_message) and last_message['type'] == "generate_report" and re.search(r'\d', message) !=None):
        print("Smash, c")
        report_no = int(re.findall(r"\d+", message)[0])-1;
        if(len(last_message['data']) < report_no):
            raise Exception(f"Requested report number is greater than number of lastest reports available.\nPlease enter a number between 1 and {len(last_message['data'])}.")
        req_search = last_message['data'][report_no];
        if(not bool(req_search['media_id'])):
            with current_app.test_client() as client:
                response = client.post('/screener/generateReport', json={"just_path": True,"constraints": req_search['query'].split(',')})
                if response.status_code == 200:
                    csv_path = response.get_json()['path']
                    
                    files = {
                        'file': open(csv_path, 'rb'),
                        'type': 'image/jpeg',
                        'messaging_product': 'whatsapp'
                    }
                    # CONTINUE HERE
                    # upload the csv to whatsapp server : https://graph.facebook.com/v18.0/137217652804256/media
                    bearer_token = current_app.config['WHATSAPP_CONFIG']['bearer_token'];
                    media_response = requests.post("https://graph.facebook.com/v18.0/137217652804256/media", headers={"Content-type": "application/json", "Authorization": f"Bearer {bearer_token}"}, files=files);
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
                    req_search['media_id'] = media_id;
                    latest_searches.update_one({"user": contact_details['wa_id']}, {"$set" : {"media_id": media_id, "last_triggered" : datetime.now()}});
                    last_messages.update_one({"_id": last_message['_id']}, {"$set" : last_message})
                else:
                    raise Exception(f"Failed to run your query. Please try again later.")
        if(bool(req_search['media_id'])):
            media_message = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": "PHONE-NUMBER",
                "type": "application/vnd.ms-excel",
                "application/vnd.ms-excel": {
                    "id" : req_search['media_id']
                }
            }
            response = requests.post("https://graph.facebook.com/v17.0/137217652804256/messages", headers={"Content-type": "application/json", "Authorization": f"Bearer {bearer_token}"}, data=media_message);
            response_data = response.json();
                
    else:
        #start convo
        print("Smash, d")
        interactive_obj = start_convo(contact_details);
    
    if(interactive_obj != None):
        message_request_body = json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to" : contact_details['wa_id'],
            "type": "interactive",
            "interactive": interactive_obj
        })
        
        print(f"Smash, messages endpoint body : {message_request_body}")
        bearer_token = current_app.config['WHATSAPP_CONFIG']['bearer_token'];
        response = requests.post("https://graph.facebook.com/v17.0/137217652804256/messages", headers={"Content-type": "application/json", "Authorization": f"Bearer {bearer_token}"}, data=message_request_body);
        response_data = response.json();
        print(f"Smash, messages response : {response_data}");

def start_convo(contact_details):
    buttons = current_app.config['BUTTONS'];
    return {
            "type": "button",
            "header": { # optional
                "type": "text",
                "text": "StockAnal"
            }, # end header
            "body": {
                "text": f"{'Hi' if random.randint(1,2) == 1 else 'Hello'} {contact_details['name']}.\nIt's not what you think it is after reading the heading. It is a Stock Analysis bot."
            },
            "footer": { # optional
                "text": "Please select an option from below"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": buttons["FETCH_BASIC_STOCKS"]
                    },
                    {
                        "type": "reply",
                        "reply": buttons['GENERATE_REPORT']
                    }
                ] 
            } # end action   
        }