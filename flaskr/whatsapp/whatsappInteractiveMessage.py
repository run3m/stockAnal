import json
import random
import re

import requests
from .. import screener
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
    print(f"Smash message type text");
    interaction = message_details['interactive'];
    db = get_db()['myDatabase'];
    body = {};
    if(interaction['type'] == 'button_reply'):
        print(f"Smash interaction type button_reply");
        button_reply = interaction[interaction['type']];
        if(button_reply != buttons[button_reply['id']]):
            raise Exception("Button configuration not mathcing. Dev : check config.py button linking")
        
        if(button_reply['id'] == 'FETCH_BASIC_STOCKS'):
            body = handle_fetch_basic_stocks(db, contact_details, buttons)
        elif(button_reply['id'] == 'FETCH_FAILED_YES'):
            body = handle_failed_basic_stocks_reply(db, contact_details, buttons)
        elif(button_reply['id'] == 'GENERATE_YES'):
            body = handle_generate_report_reply(db, contact_details)
        else:
            return
    message_request_body = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to" : contact_details['wa_id'],
        "type": "interactive",
        "interactive": body
    })
    
    print(f"Smash, messages endpoint body : {message_request_body}")
    bearer_token = current_app.config['WHATSAPP_CONFIG']['bearer_token'];
    response = requests.post("https://graph.facebook.com/v17.0/137217652804256/messages", headers={"Content-type": "application/json", "Authorization": f"Bearer {bearer_token}"}, data=message_request_body);
    response_data = response.json();
    print(f"Smash, messages response : {response_data}");

def handle_fetch_basic_stocks(db, contact_details, buttons):
    fetch_stocks_response = screener.fetch_basic_stocks()
    return internal_fetch_basic_stocks_response(fetch_stocks_response, db, contact_details, buttons)

def handle_failed_basic_stocks_reply(db, contact_details, buttons):
    with current_app.test_client() as client:
        user_last_message = db['last_messages'].find_one({'user' : contact_details['wa_id'], 'type': 'failed_pages'})
        if(user_last_message == None):
            raise Exception("No failed pages found for user");
        response = client.post('/screener/fetchBasicStocksPages', json={'pages': user_last_message['data']})
        return internal_fetch_basic_stocks_response(response.json, db, contact_details, buttons)

def internal_fetch_basic_stocks_response(fetch_stocks_response,db, contact_details, buttons):
    if(fetch_stocks_response["status"] == 'failed'):
        raise Exception(f"Oh no, could not fetch stocks. Something is off. Please come back later. Error message: {fetch_stocks_response['error']}");
    # fetch_stocks_response success
    failed_pages = fetch_stocks_response['data']['failed_pages'];

    if(len(failed_pages) > 0):
        # send partial success message;
        last_messages_collection = db['last_messages']
        last_messages_collection.update_one({"user" : contact_details['wa_id']}, {"$set": {"type" : "failed_pages",  "data" : failed_pages}}, upsert=True)
        body = {
        "type": "button",
        "header": { # optional
            "type": "text",
            "text": "Fetch basic stocks"
        }, # end header
        "body": {
            "text": f"{'Oh no, ' if random.randint(1,2) == 1 else 'Aah, '}.\nFetching is not fully completed. Missed to fetch some pages. {failed_pages}. \nDo you want to trigger them again?"
        },
        "footer": { # optional
            "text": "Please select an option from below"
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": buttons['FETCH_FAILED_YES']
                },
                {
                    "type": "reply",
                    "reply": buttons['FETCH_FAILED_NO']
                }
            ] 
        } # end action
        }
    else:
        body = {
        "type": "button",
        "header": { # optional
            "type": "text",
            "text": "Fetch basic stocks"
        }, # end header
        "body": {
            "text": f"{'Yaay! ' if random.randint(1,2) == 1 else 'Hurray! '}.\Completed fetching successfully. \nDo you want to generate a report?"
        },
        "footer": { # optional
            "text": "Please select an option from below"
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": buttons['GENERATE_YES']
                },
                {
                    "type": "reply",
                    "reply": buttons['GENERATE_YES']
                }
            ] 
        } # end action
        }
        # send full success message
    
    return body

acsdl = {
    "type": "list",
    "header": {
      "type": "text",
      "text": "Generate Report"
    },
    "body": {
      "text": "These are your latest reports constraints. You can select one or choose to enter a new query."
    },
    # "footer": {
    #   "text": "your-footer-content-here"
    # },
    "action": {
      "button": "cta-button-content",
      "sections":[
        {
          "title":"your-section_bingo",
          "rows": [
            {
              "id":"unique-row-identifier-here_a1",
              "title": "row-title_a1",
              "description": "row-description_jacmalsaksfalmlkaedf",           
            },
            {
              "id":"unique-row-identifier-here_a2",
              "title": "row-title_a2",
              "description": "row-description_jacmalsaksfalmlkaedf", 
            }
          ]
        },
        {
          "title":"your-section_lays",
          "rows": [
            {
              "id":"unique-row-identifier-here_a3",
              "title": "row-title_a3",
              "description": "row-description_jacmalsaksfalmlkaedf",           
            }
          ]
        },
      ]
    }
  }

def handle_generate_report_reply(db, contact_details):
    return acsdl;
    latest_searches =  db['latest_searches']
    user_searches_doc = latest_searches.find_one({"user" : contact_details['wa_id']})
    latest_user_searches = None
    if('searches' in user_searches_doc and  isinstance(user_searches_doc['searches'], list)):
        latest_user_searches = user_searches_doc['searches']
        if(len(user_searches_doc['searches']) > 9):
            latest_user_searches = user_searches_doc['searches'][-9:]
            user_searches_doc['searches'] = latest_user_searches
            latest_searches.update_one({"_id":user_searches_doc['_id']}, {"$set":{"searches":latest_user_searches}})
    body = {};
    if(latest_user_searches != None and isinstance(latest_user_searches, list)):
        print("return latest 10 options")
    else:
        # return message to user to directly enter the query to run
        print("Return direct give report constraints")

    return "asdf"