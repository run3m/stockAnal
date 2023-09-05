import functools
import csv
from flask import (
    Blueprint, flash, current_app, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db_config import get_db
import requests
import os
from datetime import datetime

bp = Blueprint('nifty500', __name__, url_prefix='/nifty500')

@bp.route("/updateNifty500", methods=['GET'])
def update_nifty_500():
    try:
        response = requests.get(current_app.config['URLS']['nifty_500'], headers=current_app.config['HEADERS']['nifty_500'])
        if response.status_code == 200:
            db = get_db();
            nifty500 = db['nifty500']
            # Create a list to store the parsed CSV data as dictionaries
            # Parse the CSV data
            csv_data_list = []
            csv_reader = csv.DictReader(response.content.splitlines())
            for row in csv_reader:
                csv_data_list.append(row)

            for row in csv_data_list:
                crieteria = {"symbol": row[2]}
                document = nifty500.find_one(crieteria)
                if(document is not None):
                    document['updated_on'] = datetime.now()
                    nifty500.replace_one(crieteria, document)
                else:
                    nifty500.insert_one(row)

            # if not os.path.exists('./data'):
            #     os.makedirs('./data')
            # with open('./data/ind_nifty500list.csv', 'wb') as file:
            #     file.write(response.content)
            # print('File downloaded successfully.')
            return {"status" : "success"}
        else:
            print(f'Failed to download the file. Status code: {response.status_code}')
            raise Exception("Unable to download file.");
    except Exception as e:
        print(f"Error occured in update_nifty_500 : {e}")
        return {"status" : "failed"}