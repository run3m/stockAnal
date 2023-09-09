import traceback
import pymongo
from bson.json_util import dumps

client = pymongo.MongoClient("mongodb+srv://therun3m:NPcmjPoVdBIFGled@stockanal.uvxv524.mongodb.net/?retryWrites=true&w=majority")
db = client['myDatabase']
# Define the schema using JSON Schema validation
schema = {
    "$jsonSchema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "description": "Name of the stock (required, non-empty string)"
            },
            "symbol": {
                "type": "string",
                "description": "Ticker symbol of the stock (required)",
                "unique" : True
            },
            "industry": {
                "type": "string",
                "description": "Industry of the stock (required)"
            },
            "f_url": {
                "type": "string",
                "description": "Fundamentals url for the stock (required)"
            },
            "o_url": {
                "type": "string",
                "description" : "Overview url for the stock (required)"
            },
            "created_on": {
                "type" : "date",
                "description" : "Created date"
            },
            "updated_on": {
                "type" : "date", 
                "description" : "Updated date"
            }
        },
    }
}

# Create a collection with schema validation
try:
    collection = db.create_collection('nifty500', validator=schema)
except Exception as e:
    print(f"Error {e}")
    # traceback.print_exc()

db['nifty500'].create_index([('symbol', pymongo.ASCENDING)], unique=True)


schema_headers = {
    "$jsonSchema": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": "Name of the header (required, non-empty string)"
            },
            "headers": {
                "type": "object",
                "additionalProperties": True,
                "description": "Headers of the stock (required)"
            }
        },
    }
}

# Create a collection with schema validation
try:
    collection = db.create_collection('headers', validator=schema_headers)
except Exception as e:
    print(f"Error {e}")
    traceback.print_exc()

db['headers'].create_index([('type', pymongo.ASCENDING)], unique=True)

# # Insert a document that violates the schema (e.g., missing 'age')
# invalid_user = {
#     "name": "Jane Smith",
#     "symbol": "jane.smith@example.com"
# }
# try:
#     collection.insert_one(invalid_user)
# except Exception as e:
#     print(f"Validation error: {e}")

# # Retrieve and print the documents in the collection
# for document in collection.find():
#     print(dumps(document, indent=2))
