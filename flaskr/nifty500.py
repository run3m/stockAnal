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

bp = Blueprint('nifty500', __name__, url_prefix='/nifty500')

@bp.route("/updateNifty500", methods=['GET', 'POST'])
def update_nifty_500():
    try:
        print("s", datetime.now());
        db = get_db()['myDatabase'];
        nifty500 = db['nifty500']
        csv_reader = None;
        print("e", datetime.now());
        if(request.method == 'POST'):
            print("s0", datetime.now());
            if 'file' not in request.files:
                raise Exception("Please attach file");

            file = request.files['file']
            csv_reader = csv.DictReader(io.StringIO(file.read().decode('utf-8')))
            print("e0", datetime.now());
            # csv_reader = [i for i in csv_reader];
        else:
            headers_collection = db['headers'];
            headers_doc = headers_collection.find_one({'type' : 'nifty500'})
            response = requests.get(current_app.config['URLS']['nifty_500'],  headers=headers_doc['headers'])
            if response.status_code == 200:
                # Create a list to store the parsed CSV data as dictionaries
                # Parse the CSV data
                csv_content = response.text
                csv_reader = csv.DictReader(csv_content.splitlines())
            else:
                print(f'Failed to download the file. Status code: {response.status_code}')
                raise Exception("Unable to download file.");
        
        new_docs = []
        print(csv_reader)
        
        print("s9", datetime.now());
        all_existing = nifty500.find({}, {'symbol': 1});
        print("e9", datetime.now());
        
        print("s10", datetime.now());
        all_existing_symbols = [doc['symbol'] for doc in all_existing];
        
        old_symbols = [row['Symbol'] for row in csv_reader if row['Symbol'] in all_existing_symbols];
        new_docs = [{"name" : row['Company Name'], "industry": row['Industry'], "symbol": row['Symbol'], "created_on": datetime.now()} for row in csv_reader if row['Symbol'] not in all_existing_symbols];
        print("e10", datetime.now());
        
        if(len(old_symbols) > 0):
            print("s1", datetime.now());
            nifty500.update_many({"symbol": {"$in": old_symbols}}, {"$set": {"updated_on": datetime.now()}});
            print("e1", datetime.now());
        if(len(new_docs) > 0):
            print("s2", datetime.now());
            nifty500.insert_many(new_docs)
            print("e2", datetime.now());
            
        # if not os.path.exists('./data'):
        #     os.makedirs('./data')
        # with open('./data/ind_nifty500list.csv', 'wb') as file:
        #     file.write(response.content)
        # print('File downloaded successfully.')
        return {"status" : "success"}
    except Exception as e:
        print(f"Error occured in update_nifty_500 : {e}")
        traceback.print_exc()
        return {"status" : "failed", "error": e}