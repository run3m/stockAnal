from datetime import datetime
import json
import os
import random
import re

import requests
from flask import (current_app)

from .util import generateReportAndUpload, sendReport
from ..db_config import get_db
from requests_toolbelt.multipart.encoder import MultipartEncoder


def handle_message(message_details, contact_details):
    print(f"Smash message type text");
    db = get_db()['myDatabase'];
    interactive_obj = None;
    message = str(message_details['text']['body']);
    last_messages = db['last_messages']
    latest_searches = db['latest_searches']
    last_message = last_messages.find_one({"user": contact_details['wa_id']});
    bearer_token = current_app.config['WHATSAPP_CONFIG']['bearer_token'];
    print(f"Smash last message: {last_message}")
    if(message.strip().lower() == 'hi' or message.strip().lower() == 'hello'):
        #start convo
        print("Smash, a")
        interactive_obj = start_convo(contact_details);
    elif(re.search(r'[><=\[\]]', message) != None):
        # give report
        print("Smash, b")
        req_search = {'query': message}
        generateReportAndUpload(req_search=req_search, last_message=last_message, contact_details=contact_details)
        sendReport(req_search['media_id'], contact_details=contact_details)
    elif(bool(last_message) and last_message['type'] == "generate_report" and re.search(r'\d', message) !=None):
        print("Smash, c")
        report_no = int(re.findall(r"\d+", message)[0])-1;
        if(len(last_message['data']) < report_no):
            raise Exception(f"Requested report number is greater than number of lastest reports available.\nPlease enter a number between 1 and {len(last_message['data'])}.")
        req_search = last_message['data'][report_no];
        if(not bool(req_search['media_id'])):
            generateReportAndUpload(req_search=req_search, last_message=last_message, contact_details=contact_details)
        sendReport(req_search['media_id'], contact_details=contact_details)
                
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