import json

import requests

from . import whatsappCommon
from flask import (current_app)
from .message import Message;
from ..db_config import get_db


# example
example = {
                "context": {
                  "from": "15550720472",
                  "id": "wamid.HBgMOTE4MzI4MjIzMzg2FQIAERgSRkJGOUVDNjgxMENEODNCNTE1AA=="
                },
                "from": "918328223386",
                "id": "wamid.HBgMOTE4MzI4MjIzMzg2FQIAEhgWM0VCMDlFMEE2Q0Y2MTlCMDA3MEY5NwA=",
                "timestamp": "1695722492",
                "type": "interactive",
                "interactive": {
                  "type": "button_reply",
                  "button_reply": {
                    "id": "1",
                    "title": "Fetch basic stock"
                  }
                }
              }

def handle_message(message_details, contact_details):
    buttons = current_app.config['BUTTONS'];
    print(f"Smash message type interactive");
    interaction = message_details['interactive'];
    db = get_db()['myDatabase'];
    messsage_body = {};
    if(interaction['type'] == 'button_reply'):
        print(f"Smash interaction type button_reply");
        button_reply = interaction[interaction['type']];
        if(button_reply != buttons[button_reply['id']]):
            raise Exception("Button configuration not mathcing. Dev : check config.py button linking")
        
        if(button_reply['id'] == 'FETCH_BASIC_STOCKS'):
            messsage_body = whatsappCommon.handle_fetch_basic_stocks(db, contact_details)
        elif(button_reply['id'] == 'FETCH_FAILED_YES'):
            messsage_body = whatsappCommon.handle_failed_basic_stocks_reply(db, contact_details)
        elif(button_reply['id'] == 'GENERATE_YES' or button_reply['id'] == 'GENERATE_REPORT'):
            messsage_body = whatsappCommon.handle_generate_report_reply(db, contact_details)
        elif(button_reply['id'] == 'SHOW_FIELDS'):
            # write for show fields
            messsage_body = whatsappCommon.handle_show_fields()
        else:
            raise Exception("Button configuration not mathcing. Dev : check config.py button linking")
        
    print(f"Smash message_body : {messsage_body}")
    base = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to" : contact_details['wa_id']
    }
    message_request_body = json.dumps({**base, **messsage_body})
    
    print(f"Smash, messages endpoint body : {message_request_body}")
    bearer_token = current_app.config['WHATSAPP_CONFIG']['bearer_token'];
    response = requests.post("https://graph.facebook.com/v17.0/137217652804256/messages", headers={"Content-type": "application/json", "Authorization": f"Bearer {bearer_token}"}, data=message_request_body);
    response_data = response.json();
    print(f"Smash, messages response : {response_data}");
    