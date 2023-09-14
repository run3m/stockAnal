
from .db_config import get_db
from flask import (
    Blueprint
)
import pymongo



bp = Blueprint('fetchCommon', __name__, url_prefix='/data')

@bp.route("/fetchCommon", methods=['GET', 'POST'])
def fetchCommon():

    try:
        client = get_db()
        db = client['myDatabase']
        scr_init = db['scr_init']
    except ServerSelectionTimeoutError:
        error_response = {"error": "MongoDB connection error"}
        @app.route('/api')
        def handle_mongodb_connection_error():
            return jsonify(error_response)
    common_fields = {} 

    for document in scr_init.find({}):  # Retrieve all documents
        for field in document.keys():  # Iterate over the fields in each document
            if field in common_fields:
                common_fields[field] += 1
            else:
                common_fields[field] = 1


    

    return common_fields;