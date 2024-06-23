import functools
import csv
import io
import traceback
from flask import (
    Blueprint, flash, current_app, g, redirect, render_template, request, session, url_for, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db_config import get_db
import requests
import os
from datetime import datetime
import requests_cache

from . import models
import json
import yfinance as yf
import math


bp = Blueprint('warren', __name__, url_prefix='/warren')


@bp.route("/getSheetsForStock", methods=['POST'])
def getSheetsForStock():
    try:
        query_params = request.args

        db = get_db()['myDatabase']
        # Get all rows from warren_fetch_status where full_fetched : false
        warren_fetch_status_collection = db['warren_fetch_status']
        stock = db['nifty500'].find_one({"symbol":query_params.get("symbol")})
        if(stock is None):
            return jsonify({"status": "fail", "error":"No stock exists with given symbol"}),400
        
        warren_unfetched = warren_fetch_status_collection.find({"_id":stock["_id"]})

        stock_ticker = yf.Ticker(f"{stock['symbol']}.NS")
        
        # For each stock in warren_fetch_status, fetch : income, balance sheet, cashflow(4 years, 5 quaters)
        statement_data = []

        # Yearly statements
        income_statement_yearly = stock_ticker.get_income_stmt(as_dict=True, pretty=True, freq="yearly")
        statement_data.extend(create_statement_documents(stock_id=stock['_id'], statement_type=models.StatementType.INCOME_STATEMENT, freq="yearly", data=income_statement_yearly))
        income_statement_yearly = {str(key): value for key,value in income_statement_yearly.items()}

        balance_sheet_yearly = stock_ticker.get_balance_sheet(as_dict=True, pretty=True, freq="yearly")
        statement_data.extend(create_statement_documents(stock_id=stock['_id'], statement_type=models.StatementType.BALANCE_SHEET, freq="yearly", data=balance_sheet_yearly))
        balance_sheet_yearly = {str(key): value for key,value in balance_sheet_yearly.items()}

        cash_flow_statement_yearly = stock_ticker.get_cash_flow(as_dict=True, pretty=True, freq="yearly")
        statement_data.extend(create_statement_documents(stock_id=stock['_id'], statement_type=models.StatementType.CASHFLOW_STATEMENT, freq="yearly", data=cash_flow_statement_yearly))
        cash_flow_statement_yearly = {str(key): value for key,value in cash_flow_statement_yearly.items()}

        # Quaterly statements
        income_statement_quaterly = stock_ticker.get_income_stmt(as_dict=True, pretty=True, freq="quarterly")
        statement_data.extend(create_statement_documents(stock_id=stock['_id'], statement_type=models.StatementType.INCOME_STATEMENT, freq="quarterly", data=income_statement_quaterly))
        income_statement_quaterly = {str(key): value for key,value in income_statement_quaterly.items()}

        balance_sheet_quaterly = stock_ticker.get_balance_sheet(as_dict=True, pretty=True, freq="quarterly")
        statement_data.extend(create_statement_documents(stock_id=stock['_id'], statement_type=models.StatementType.BALANCE_SHEET, freq="quarterly", data=balance_sheet_quaterly))
        balance_sheet_quaterly = {str(key): value for key,value in balance_sheet_quaterly.items()}

        cash_flow_statement_quaterly = stock_ticker.get_cash_flow(as_dict=True, pretty=True, freq="quarterly")
        statement_data.extend(create_statement_documents(stock_id=stock['_id'], statement_type=models.StatementType.CASHFLOW_STATEMENT, freq="quarterly", data=cash_flow_statement_quaterly))
        cash_flow_statement_quaterly = {str(key): value for key,value in cash_flow_statement_quaterly.items()}
        
        # Fetch each of the sheet and store in db(4 at a time, 5 at a time or 9 at a time.)
        statements_collection = db['statements']
        inserted_statements = statements_collection.insert_many(statement_data)
        print("Inserted Document count : ", len(inserted_statements.inserted_ids), " Statements list count : ", len(statement_data))
        
        updated_status = warren_fetch_status_collection.update_one({"_id":stock["_id"]}, {'$inc': {'full_fetched': True}})
        print(updated_status.modified_count)
        
        return {"income_statement_yearly" : income_statement_yearly, "balance_sheet_yearly": balance_sheet_yearly, "cash_flow_statement_yearly": cash_flow_statement_yearly, "income_statement_quaterly":income_statement_quaterly, "balance_sheet_quaterly":balance_sheet_quaterly, "cash_flow_statement_quaterly":cash_flow_statement_quaterly}
        # return {"income_statement_yearly" : income_statement_yearly}
        # After fetch for each statement is done change fetch status of that sheet to true
    except Exception as e:
        print("Error")


def create_statement_documents(stock_id, statement_type:models.StatementType, freq, data:dict) -> list[models.Statement]:
    documents:list[models.Statement] = []
    for key, value in data.items():
        year = int(key.year)
        document:models.Statement=None
        if(freq == 'quarterly'):
            quarter = math.ceil(int(key.month)/3)
            document: models.Statement = models.Statement(stock_id=stock_id, statement_type=statement_type, year=year, quarter=quarter, time_frame=freq, data=value, statement_date=key.to_pydatetime(), date=datetime.now())
        else:
            document: models.Statement = models.Statement(stock_id=stock_id, statement_type=statement_type, year=year, time_frame=freq, data=value, statement_date=key.to_pydatetime(), date=datetime.now())
        if(document is not None):
            documents.append(document.model_dump(exclude_none=True))
    return documents

@bp.route("/warren", methods=['POST'])
def fetchStocks():
    try:
        db = get_db()['myDatabase']
        # Get all rows from warren_fetch_status where full_fetched : false
        warren_fetch_status_collection = db['warren_fetch_status']
        warren_unfetched = warren_fetch_status_collection.find({"full_fetched":False})

        stocks = db['nifty500'].find()
        # For each stock in warren_fetch_status, fetch : income, balance sheet, cashflow(4 years, 5 quaters)
        

        # Fetch each of the sheet and store in db(4 at a time, 5 at a time or 9 at a time.)

        # After fetch for each statement is done change fetch status of that sheet to true
    except Exception as e:
        print("Error")

@bp.route("/resetFetchStatus", methods=['POST'])
def resetFetchStatus():
    try:
        db = get_db()['myDatabase']
        nifty500 = db['nifty500']

        nifty500_records = nifty500.find()

        warren_status_records = [models.WarrenFetchStatus(stock_id=nifty500_record['_id']).model_dump(exclude_none=True) for nifty500_record in nifty500_records]
        
        warren_fetch_status_collection = db['warren_fetch_status']
        
        # Deleting all records from warren_fetch_status before adding them again.
        warren_fetch_status_collection.delete_many({})

        # Insert all records into warren_fetch_status
        warren_fetch_status_insert_data = warren_fetch_status_collection.insert_many(warren_status_records)

        return {"staus":"success", "inserted_records" : [str(inserted_id) for inserted_id in warren_fetch_status_insert_data.inserted_ids]}
    except Exception as e:
        print("Error occured in resetFetchStatus : ", e)
        return {"status": "error", "error" : e}


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