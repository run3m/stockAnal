import json
import random
import re

import requests
from .. import screener
from flask import (current_app)
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
    print(f"Smash message type text");
    interaction = message_details['interactive'];
    if(interaction['type'] == 'button_reply'):
        print(f"Smash interaction type button_reply");
        button_reply = interaction[interaction['type']];
        if(button_reply != buttons[button_reply['id']]):
            raise Exception("Button configuration not mathcing. Dev : check config.py button linking")
        
        if(button_reply['id'] == '1'):
            response = screener.fetch_basic_stocks();
            if(response["status"] == 'failed'):
                raise Exception(f"Oh no, could not fetch stocks. Something is off. Please come back later. Error message: {response['error']}");
            # response success
            

    
    message_request_body = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to" : contact_details['wa_id'],
        "type": "interactive",
        "interactive": interactive_obj
    })
    
    print(f"Smash, messages endpoint body : {message_request_body}")
    bearer_token = "EAAN7ZAYP8husBO3ZARS537OczlY1oSGFTBugkzJy1x9kDTSEtsDDQZAazLrNWLvj6iD1zZAJCOq9YtgYJGSruFdGKkZC5xBTl9IEJidD6lKpOQICFsLTOhdCclTFnKrqWCxMJHdHtKUDXBd7tdkYOqKgZAZAxJYwug71fnzEP3FItBf4yLz6fUNLyjr1PGorXwXXpFxcmRhbvkwzJnKUrgZD"
    response = requests.post("https://graph.facebook.com/v17.0/137217652804256/messages", headers={"Content-type": "application/json", "Authorization": f"Bearer {bearer_token}"}, data=message_request_body);
    response_data = response.json();
    print(f"Smash, messages response : {response_data}");
