
from .db_config import get_db
from flask import (
    Blueprint,
    jsonify
)
import pymongo



bp = Blueprint('fetchCommon', __name__, url_prefix='/data')

@bp.route("/fetchCommon", methods=['GET', 'POST'])
def fetchCommon():
    # we'll add to common
    try:
        client = get_db()
        db = client['myDatabase']
        scr_init = db['scr_init']
        fields = []
        for document in scr_init.find({}):  # Retrieve all documents
            for field in document.keys():  # Iterate over the fields in each document
                if field not in fields:
                    fields.append(field)
        return {"status": "success", "data" : fields};
    except Exception as e:
        return {"status": "failed", "error": str(e)}