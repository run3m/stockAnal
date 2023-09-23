import traceback
import requests
from bs4 import BeautifulSoup
from .db_config import get_db
from flask import (
    Blueprint, flash, current_app, g, redirect, render_template, request, session, url_for
)
import pymongo

from werkzeug.security import check_password_hash, generate_password_hash

host = "https://trendlyne.com"
url = "/member/api/ac_snames/stock/?term="
header = {
    'authority': 'trendlyne.com',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': '_ga=GA1.1.1782871925.1693233109; g_state={"i_l":0}; .trendlyne=6s5xl8mk4tn2f71o9n7y70d14wcoksqw; _clck=9kj3p8|2|fej|0|1335; csrftoken=lzCaJa6a8ErLbmsN6KjRZmvn8VNjsj1LeJwzYIiHQxyzxyuIpxpY5tQDmwYneSAV; _ga_7F29Q8ZGH0=GS1.1.1694113029.3.1.1694113057.32.0.0',
    'referer': 'https://trendlyne.com/equity/139596/RVNL/rail-vikas-nigam-ltd/',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

def hit(url : str ,header : str ,ticker :str) :
    o_url = None;
    f_url = None; 

    try:
        response = requests.get(host+url+ticker, headers=header)

        if response.status_code == 200:
            json_data = response.json()
            o_url = json_data[0]["nexturl"]
            try:
                response2 = requests.get(host+o_url, headers=header)

                try:
                    soup = BeautifulSoup(response2.text, 'html.parser')
                except:
                    print(response2.text , type(response2), str(response2))


                    return o_url , None ;

                element = soup.find(attrs={"data-tablesurl": True})

                data_tablesurl = element['data-tablesurl']

                if data_tablesurl:
                    print(data_tablesurl) 
                    f_url = data_tablesurl ;
                else:
                    print("Div with id", div_id_to_find, "not found in the HTML file.")


            except requests.exceptions.RequestException as e2:
                print(f"An error occurred: {e}")

        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    return o_url , f_url ;


bp = Blueprint('updateUrls', __name__, url_prefix='/data')

@bp.route("/updateUrls", methods=['GET', 'POST'])
def updateUrls():

    try:
        client = get_db()
        db = client['myDatabase']
        nifty500 = db['nifty500']
    except ServerSelectionTimeoutError:
        error_response = {"error": "MongoDB connection error"}
        @app.route('/api')
        def handle_mongodb_connection_error():
            return jsonify(error_response)
    
    cursor = nifty500.find({})
    sym = []
    i =0
    for document in cursor:
        sym = document.get("symbol")
        o_url , f_url = hit(url,header,sym)
        nifty500.update_one({"symbol": sym}, {"$set": {"o_url": o_url}})
        nifty500.update_one({"symbol": sym}, {"$set": {"f_url": f_url}})
    return "Succesful";