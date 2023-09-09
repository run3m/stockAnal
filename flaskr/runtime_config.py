import functools
import csv
import io
import traceback
from flask import (
    Blueprint, flash, current_app, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db_config import get_db
import requests
import os
from datetime import datetime
import re

bp = Blueprint('runtime_config', __name__, url_prefix='/runtimeConfig')

@bp.route('/refreshHeaders', methods=['POST'])
def refresh_headers():
    try:
        form_data = request.form
        
        db = get_db()['myDatabase'];
        headers_collection = db['headers'];
        
        type = form_data.get('type');
        curl_command = form_data.get('command')
        # if 'file' not in request.files:
        #     raise Exception("Please attach file");

        # file = request.files['file']
        headers = curl_to_headers(curl_command)
                    
        if(type == 'nifty500'):
            headers_collection.update_one({'type': 'nifty500'}, {'$set':  {'type': 'nifty500', 'headers' : headers}}, upsert=True);
        elif(type == 'trendlyne'):
            headers_collection.update_one({'type': 'trendlyne'}, {'$set':  {'type': 'trendlyne', 'headers' : headers}}, upsert=True);
        else:
            raise Exception("Given refresh headers type parameter is not supported.")
        
        return {"status" : "success"}
    except Exception as e:
        print(f"Error occured in update_nifty_500 : {e}")
        traceback.print_exc()
        return {"status" : "failed", "error": e}

def curl_to_headers(curl_command):
    headers = {}
    
    # Extract headers from the curl command using regular expressions
    header_pattern = r"-H '([^:]+): ([^']*)'"
    matches = re.findall(header_pattern, curl_command)
    print(matches)
    for match in matches:
        print(match)
        header_name, header_value = match
        headers[header_name] = header_value
    
    return headers