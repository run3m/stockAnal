import json

import requests

from . import whatsappCommon
from flask import current_app
from .message import Message


# example
example = {
    "context": {
        "from": "15550720472",
        "id": "wamid.HBgMOTE4MzI4MjIzMzg2FQIAERgSRkJGOUVDNjgxMENEODNCNTE1AA==",
    },
    "from": "918328223386",
    "id": "wamid.HBgMOTE4MzI4MjIzMzg2FQIAEhgWM0VCMDlFMEE2Q0Y2MTlCMDA3MEY5NwA=",
    "timestamp": "1695722492",
    "type": "interactive",
    "interactive": {
        "type": "button_reply",
        "button_reply": {"id": "1", "title": "Fetch basic stock"},
    },
}


def handle_message(message_details, contact_details):
    buttons = current_app.config["BUTTONS"]
    print(f"Smash message type interactive")
    interaction = message_details["interactive"]
    message_body = {}
    if interaction["type"] == "button_reply":
        print(f"Smash interaction type button_reply")
        button_reply = interaction[interaction["type"]]
        if button_reply != buttons[button_reply["id"]]:
            raise Exception(
                "Button configuration not mathcing. Dev : check config.py button linking"
            )

        if button_reply["id"] == "FETCH_BASIC_STOCKS":
            message_body = whatsappCommon.handle_fetch_basic_stocks(contact_details)
        elif button_reply["id"] == "FETCH_FAILED_YES":
            message_body = whatsappCommon.handle_failed_basic_stocks_reply(
                contact_details
            )
        elif (
            button_reply["id"] == "GENERATE_YES"
            or button_reply["id"] == "GENERATE_REPORT"
        ):
            message_body = whatsappCommon.handle_generate_report_reply(contact_details)
        elif button_reply["id"] == "SHOW_FIELDS":
            # write for show fields
            message_body = whatsappCommon.handle_show_fields()
        else:
            raise Exception(
                "Button configuration not mathcing. Dev : check config.py button linking"
            )

    base = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": contact_details["wa_id"],
    }
    print(f"Smash message_body : {message_body}")
    message_request_body = json.dumps({**base, **message_body})

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
