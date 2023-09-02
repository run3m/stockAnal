from flask import Flask
from readFromUrl import readUrl 
# Create an instance of the Flask class
app = Flask(__name__)

# Define a route and a view function
@app.route('/')
def hello():
    
    return 'Hello, World!'

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
