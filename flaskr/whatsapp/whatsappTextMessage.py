import json
import random
import re

import requests
from flask import (current_app)

def handle_message(message_details, contact_details):
    print(f"Smash message type text");
    interactive_obj = None;
    message = str(message_details['text']['body']);
    if(message.strip().lower() == 'hi' or message.strip().lower() == 'hello'):
        #start convo
        print("Smash, a")
        interactive_obj = start_convo(contact_details);
    elif(re.search(r'[><=\[\]]', message)):
        # give report
        print("Smash, b")
    else:
        #start convo
        print("Smash, c")
        interactive_obj = start_convo(contact_details);
    
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