from datetime import datetime
import json
import os
import random
import re

import requests
from flask import current_app
import joblib

from . import whatsappCommon

from . import util
from ..db_config import get_db

make_prediction = joblib.load("message_classification_function.pkl")


def handle_message(message_details, contact_details):
    print(f"Smash message type text")
    db = get_db()["myDatabase"]
    interactive_obj = None
    message_object = None
    message = str(message_details["text"]["body"])
    last_messages = db["last_messages"]
    last_message = last_messages.find_one({"user": contact_details["wa_id"]})
    bearer_token = current_app.config["WHATSAPP_CONFIG"]["bearer_token"]
    print(f"Smash last message: {last_message}")
    pred = make_prediction([message])
    print("Smash prediction : ", pred)
    print("Smash prediction type : ", pred[0])
    prediction_type = pred[0]

    if re.search(r"[><=\[\]]", message) != None:
        # give report
        req_search = {"query": message}
        util.generateReportAndUpload(
            req_search=req_search,
            last_message=last_message,
            contact_details=contact_details,
            isNewQuery=True
        )
        return util.sendReport(req_search["media_id"], contact_details=contact_details)
    elif (
        bool(last_message)
        and last_message["type"] == "generate_report"
        and re.search(r"\d", message) != None
    ):
        report_no = int(re.findall(r"\d+", message)[0]) - 1
        if len(last_message["data"]) < report_no:
            raise Exception(
                f"Requested report number is greater than number of lastest reports available.\nPlease enter a number between 1 and {len(last_message['data'])}."
            )
        req_search = last_message["data"][report_no]
            
        stocks = db["scr_init"]
        first_stock = stocks.find_one({"sno": 1})
        if not bool(req_search["media_id"]) or req_search["last_triggered"] < first_stock["last_interaction"]:
            util.generateReportAndUpload(
                req_search=req_search,
                last_message=last_message,
                contact_details=contact_details,
            )
        return util.sendReport(req_search["media_id"], contact_details=contact_details)
    elif prediction_type == "start_convo":
        interactive_obj = start_convo(contact_details)
    elif prediction_type == "show_fields":
        message_object = whatsappCommon.handle_show_fields()
    elif prediction_type == "fetch_basic_stocks":
        message_object = whatsappCommon.handle_fetch_basic_stocks(contact_details)
    elif prediction_type == "retry_basic_fetch":
        message_object = whatsappCommon.handle_failed_basic_stocks_reply(
            contact_details
        )
    elif prediction_type == "old_reports":
        message_object = whatsappCommon.handle_generate_report_reply(contact_details)
    elif prediction_type == "generate_new_report":
        interactive_obj = whatsappCommon.handle_generate_report_reply(contact_details)
    else:
        # start convo
        print("Smash, d")
        interactive_obj = start_convo(contact_details)

    if not bool(interactive_obj) or not bool(message_object):
        message_request_body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": contact_details["wa_id"],
        }
        if bool(interactive_obj):
            message_request_body = json.dumps(
                {
                    **message_request_body,
                    "type": "interactive",
                    "interactive": interactive_obj,
                }
            )
        elif bool(message_object):
            message_request_body = json.dumps(
                {**message_request_body, **message_object}
            )
        print(f"Smash, messages endpoint body : {message_request_body}")
        bearer_token = current_app.config["WHATSAPP_CONFIG"]["bearer_token"]
        response = requests.post(
            current_app.config["WHATSAPP_CONFIG"]["message_url"],
            headers={
                "Content-type": "application/json",
                "Authorization": f"Bearer {bearer_token}",
            },
            data=message_request_body,
        )
        response_data = response.json()
        print(f"Smash, messages response : {response_data}")


def start_convo(contact_details):
    buttons = current_app.config["BUTTONS"]
    return {
        "type": "button",
        "header": {"type": "text", "text": "StockAnal"},  # optional  # end header
        "body": {
            "text": f"{'Hi' if random.randint(1,2) == 1 else 'Hello'} {contact_details['name']}.\nIt's not what you think it is after reading the heading. It is a Stock Analysis bot."
        },
        "footer": {"text": "Please select an option from below"},  # optional
        "action": {
            "buttons": [
                {"type": "reply", "reply": buttons["FETCH_BASIC_STOCKS"]},
                {"type": "reply", "reply": buttons["GENERATE_REPORT"]},
            ]
        },  # end action
    }
