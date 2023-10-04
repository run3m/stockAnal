import datetime
import json
import traceback
import requests

from . import whatsappTextMessage
from . import whatsappInteractiveMessage
from ..db_config import get_db
from flask import (
    Blueprint, flash, current_app, g, redirect, render_template, request, session, url_for, jsonify, Response
)
import pymongo
import re;
import random;

# from .. import calls;

bp = Blueprint('webhook', __name__, url_prefix='/whatsapp')

@bp.route("/webhook", methods=['POST', 'GET'])
def webhook():    
    if(request.method == 'GET'):
      print(f"Smash, GET method(verify webhook) triggered : {request.args}");
      if (
        request.args['hub.mode'] == 'subscribe' and
        request.args['hub.verify_token'] == 'tysonitis'):   
            response = Response(request.args['hub.challenge'], status=200)
            response.headers['Content-Type'] = 'text/plain'
            return response;
    
    elif(request.method == 'POST'):
        try:
            # Handle incoming messages here
            # check if it is a message from user or just a status trigger message
            # You can extract message content, sender information, etc., from 'data'
            body = request.get_json()
            print(f"Smash, POST method(incoming messages and replies) triggered : {body}")
            if(body['entry']):
                entries = body['entry'];
                if(is_ongoing_or_status_request(entries[0])):
                   return Response(status=200)
               
                if(len(entries) > 1):
                    print("RECEIVED MORE THAN 1 ENTRY");
                else:
                    # if(calls[''])
                    handle_entry(entries[0]);
        except Exception as e:
            print(f"Error occured in send whatsapp message : {e}")
            traceback.print_exc()
        finally:
            calls = current_app.config['calls'];
            unique_id = ['changes'][0]['value']['messages'][0]['id'];
            if(entries[0].get(unique_id, None) != None):
                print(entries[0].get(unique_id))
                calls[entries[0].get(unique_id)] = None
        return Response(status=200)
    



def is_ongoing_or_status_request(entry):
    unique_id = None;
    try:
        unique_id = entry['changes'][0]['value']['messages'][0]['id'];
    except Exception:
        try:
            unique_id = entry['changes'][0]['value']['statuses'][0]['id'];
            if(unique_id != None and len(unique_id)>0):
                return True;
        except:
            raise Exception("Unable to read neither message id nor message status")

    calls = current_app.config['calls']
    if(unique_id in calls):
        return True

    calls[unique_id] = True
    return False
    

def handle_entry(entry):
    # get contact name.
    changes_obj = entry['changes'][0]
    contact_details = None;
    if ('contacts' in changes_obj['value']):
        contact_details = get_contact_details(changes_obj['value']['contacts'][0]);
    
    if ('messages' in changes_obj['value']):
        # get user message
        message_details = changes_obj['value']['messages'][0];
        
        if('type' in message_details):
            if(message_details['type'] == "text"):
                whatsappTextMessage.handle_message(message_details, contact_details);
            elif(message_details['type'] == "interactive"):
                # handle interactive message
                whatsappInteractiveMessage.handle_message(message_details, contact_details)
    
def get_contact_details(contact):
    return {'name' : contact['profile']['name'], 'wa_id': contact['wa_id']};