import functools
import csv
import io
import re
import traceback
from flask import (
    Blueprint, flash, current_app, g, redirect, render_template, request, session, url_for , send_file
)
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.errors import BulkWriteError

from .db_config import get_db
import requests
import os
from datetime import datetime
from bs4 import BeautifulSoup
import tempfile
import json
import csv
bp = Blueprint('screenerio', __name__, url_prefix='/screener')
tmp_file = ''
@bp.route("/fetchBasicStocks", methods=['GET'])
def fetch_basic_stocks():
    try:
        print("s01", datetime.now());
        db = get_db()['myDatabase'];
        print("e01", datetime.now());
        headers_collection = db['headers'];
        print("s02", datetime.now());
        headers_doc = headers_collection.find_one({'type' : 'screener'})
        print("e02", datetime.now());
        url = current_app.config['URLS']['screener']
        print("s03", datetime.now());
        query_response = requests.get(url, headers=headers_doc['headers']);
        print("e03", datetime.now());
        stock_data = []
        headers = []
        failed_pages = []
        failed_pages_messages = {}
        if query_response.status_code == 200:
            # Parse the HTML content of the response
            print('Page 1')
            soup = BeautifulSoup(query_response.text, 'html.parser')
            pages_html = soup.select_one('div[data-page-info=""]')
            print(pages_html);
            total_pages = int(pages_html.string.split('of')[1].strip());
            
            headers, stock_data = fetch_data(soup, stock_data, True);
            
            if(total_pages > 1):
                    for i in range(2, total_pages + 1):
                        try:
                            page_url = url.replace("&page=1", f"&page={i}");
                            query_response = requests.get(page_url, headers=headers_doc['headers']);
                            if query_response.status_code == 200:
                                # Parse the HTML content of the response
                                print(f'Page {i}')
                                soup = BeautifulSoup(query_response.text, 'html.parser')
                                stock_data = fetch_data(soup, stock_data)[0];
                            else:
                                raise Exception(f"200 response not received from screener for page : {i}. Response : {query_response}")
                        except Exception as e:
                            failed_pages.append(i);
                            failed_pages_messages[i] = str(e);
                            print(f'Failed : page {i}, {e}')
                            continue;
        
        insert_result = None;
        screener_data_collection = db['scr_init'];
        print("s0", datetime.now());
        existing_docs = screener_data_collection.find({}, {"company_id": 1});
        print("e0", datetime.now());
        existing_companies = [doc['company_id'] for doc in existing_docs]
        try:
            docs = [dict(zip(headers, row)) for row in stock_data];
            existing_company_ids = [i['company_id'] for i in docs if i['company_id'] in existing_companies];
            
            print("s1", datetime.now());
            screener_data_collection.delete_many({"company_id": {"$in": existing_company_ids}});
            print("e1", datetime.now());
            insert_result = screener_data_collection.insert_many(docs);
            print("e2", datetime.now());
        except BulkWriteError as e:
            # Handle the error (e.g., log it, skip the problematic document, etc.)
            # we can add all those that fail insert to an array and trigger update_many for those.
            for error in e.details['writeErrors']:
                print("Error:", error)
        
        return {"status" : "success", "data": {"headers" : headers, "values" : stock_data, "inserted_ids": [str(id) for id in insert_result.inserted_ids], "failed_pages" : failed_pages, "count": len(stock_data)}}

    except Exception as e:
        print(f"Error occured in update_nifty_500 : {e}")
        traceback.print_exc()
        return {"status" : "failed", "error": str(e), "data": {"headers" : headers, "values" : stock_data, "failed_pages" : failed_pages, "failed_pages_messages": failed_pages_messages, "count": len(stock_data)}}
    
    
    
    
    
@bp.route("/fetchBasicStocksPages", methods=['POST'])
def fetch_basic_stocks_pages():
    try:
        stock_data = []
        headers = []
        failed_pages = []
        failed_pages_messages = {}
        body = {}
        try:
            body = request.get_json()
        except Exception as e:
            raise Exception(f"Failed to parse JSON data: {e}")
        
        if('pages' not in body):
            raise Exception(f"Please enter the pages you want to fetch as list in request body")
        pages = body['pages']
        if(pages == None or len(pages) == 0):
            raise Exception('Please enter the pages to fetch.')
        
        print("s01", datetime.now());
        db = get_db()['myDatabase'];
        print("e01", datetime.now());
        headers_collection = db['headers'];
        print("s02", datetime.now());
        headers_doc = headers_collection.find_one({'type' : 'screener'})
        print("e02", datetime.now());
        url = current_app.config['URLS']['screener']
            
        page_url = url.replace("&page=1", f"&page={pages[0]}");
        print("s03", datetime.now());
        query_response = requests.get(page_url, headers=headers_doc['headers']);
        print("e03", datetime.now());
        if query_response.status_code == 200:
            # Parse the HTML content of the response
            print(f'Page {pages[0]}')
            soup = BeautifulSoup(query_response.text, 'html.parser')
            pages_html = soup.select_one('div[data-page-info=""]')
            print(pages_html);
            total_pages = int(pages_html.string.split('of')[1].strip());
            
            headers, stock_data = fetch_data(soup, stock_data, True);
            
            if(total_pages > 1 and len(pages)>1):
                    for i in pages[1:]:
                        try:
                            if(total_pages < i):
                                raise Exception(f"Page {i} is greater than total available pages({total_pages}) to fetch")
                            page_url = url.replace("&page=1", f"&page={i}");
                            query_response = requests.get(page_url, headers=headers_doc['headers']);
                            if query_response.status_code == 200:
                                # Parse the HTML content of the response
                                print(f'Page {i}')
                                soup = BeautifulSoup(query_response.text, 'html.parser')
                                stock_data = fetch_data(soup, stock_data)[0];
                            else:
                                raise Exception(f"200 response not received from screener for page : {i}. Response : {query_response}")
                        except Exception as e:
                            failed_pages.append(i);
                            failed_pages_messages[i] = str(e);
                            print(f'Failed : page {i}, {e}')
                            continue;
        
        insert_result = None;
        screener_data_collection = db['scr_init'];
        print("s0", datetime.now());
        existing_docs = screener_data_collection.find({}, {"company_id": 1});
        print("e0", datetime.now());
        existing_companies = [doc['company_id'] for doc in existing_docs]
        try:
            docs = [dict(zip(headers, row)) for row in stock_data];
            existing_company_ids = [i['company_id'] for i in docs if i['company_id'] in existing_companies];
            
            print("s1", datetime.now());
            screener_data_collection.delete_many({"company_id": {"$in": existing_company_ids}});
            print("e1", datetime.now());
            insert_result = screener_data_collection.insert_many(docs);
            print("e2", datetime.now());
        except BulkWriteError as e:
            # Handle the error (e.g., log it, skip the problematic document, etc.)
            # we can add all those that fail insert to an array and trigger update_many for those.
            for error in e.details['writeErrors']:
                print("Error:", error)
        
        return {"status" : "success", "data": {"headers" : headers, "values" : stock_data, "inserted_ids": [str(id) for id in insert_result.inserted_ids], "failed_pages" : failed_pages, "count": len(stock_data)}}

    except Exception as e:
        print(f"Error occured in update_nifty_500 : {e}")
        traceback.print_exc()
        return {"status" : "failed", "error": str(e), "data": {"headers" : headers, "values" : stock_data, "failed_pages" : failed_pages, "failed_pages_messages": failed_pages_messages, "count": len(stock_data)}}
  
    
def fetch_data(soup, stock_data, header_req = False):
    return_val = [];
    table_markup = soup.find('table', class_=lambda x: x and 'data-table' in x.split())
    table_body = table_markup.tbody
    trs = table_body.find_all('tr');
    
    if(header_req):
        headers = ['company_id'];
        header_ths = trs[0].find_all('th');
        for th in header_ths:
            if(th.has_attr('data-tooltip')):
                valid_header = str(th['data-tooltip']).lower().replace(' ', '_');
                valid_header = re.sub(r'[^a-zA-Z0-9_]', '', valid_header);
                headers.append(valid_header)
            else:
                headers.append(get_cleaned_header(th.a.string));
        headers.append('link');
        headers.append('last_interaction')
        return_val.append(headers)
    
    for tr in trs:
        if(tr and tr.has_attr('data-row-company-id')):
            values = [tr['data-row-company-id']]
            direct_link = None
            for i, td in enumerate(tr.find_all('td')):
                value = ""
                if(td.find('a')):
                    value = td.a.string
                    direct_link = f"https://www.screener.in{td.a['href']}"
                else:
                    value = td.string
                value = get_cleaned_string(value)
                value = string_to_float(value);
                values.append(value)
            values.append(direct_link)
            values.append(datetime.now())
            # print(f"adding values : {values}");
            stock_data.append(values);
            
    return_val.append(stock_data);
    return return_val
    
@bp.route("/generateReport", methods=['POST'])
def generate_report():
    reports = []
    body = {}
    try:
        try:
            body = request.get_json()
        except Exception as e:
            raise Exception(f"Failed to parse JSON data: {e}")
        if('constraints' not in body):
            raise Exception(f"Please enter the constraints you want to check for as list in request body")
        db = get_db()['myDatabase']
        scr_init_collection = db['scr_init'];
        docs = scr_init_collection.find();
        # constraints = body['constraints'];
        for doc in docs:
            for key, value in doc.items():
                locals()[key] = value
            report = {'name': locals()['name'], 'company_id': locals()['company_id'], 'link': locals()['link']};
            scores = {}
            score = 0;
            for constraint in body['constraints']:
                try:
                    print(constraint)
                    if(eval(constraint)):
                        scores[constraint] = 1
                        score += 1;
                    else:
                        scores[constraint] = 0
                except Exception as e:
                    print(f"Error occured in generate report : constraint: {constraint} : {e}")
                    traceback.print_exc()
                    scores[constraint] = 0
            report['scores'] = scores;
            report['score'] = score;
            reports.append(report);
             
        csv_path = writeTocsv(reports)


            
        return send_file(csv_path,
                as_attachment=True,
                download_name='output.csv',
                mimetype='text/csv'
            );
    except Exception as e:
        print(f"Error occured in generate report : {e}")
        traceback.print_exc()
        return {"status" : "failed", "error": str(e), "data": reports}
    
# @bp.after_request
# def remove_file(response):
#     global tmp_file
#     os.remove(tmp_file) # Delete file
#     print(tmp_file + "removed")
#     return response

def get_cleaned_header(input_string):
    if(input_string):
        input_string = re.sub(r'\n+', '', str(input_string))
        input_string = input_string.lower().strip().replace(" ", "_");
        return re.sub(r'[^a-zA-Z0-9_]', '', input_string);
    return input_string 
    
def get_cleaned_string(input_string):
    if(input_string):
        return re.sub(r'\n\s+', '', input_string)

def string_to_float(input_string):
    try:
        float_value = float(input_string)
        return float_value
    except Exception:
        return input_string
    
def flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def writeTocsv(reports):
    global tmp_file 
    tmp = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    tmp_file = tmp.name
    data = json.loads(json.dumps(reports))
    fieldnames= list(flatten(data[0]).keys())
    dic = {}
    for i in fieldnames:
        dic[i] = i

    f = open(tmp_file, 'w')

    try:
        writer = csv.DictWriter(f, fieldnames=fieldnames) 
        writer.writerow(dic)
        for row in data:
            writer.writerow(flatten(row))

    finally:
        f.close()   
    return tmp_file;
