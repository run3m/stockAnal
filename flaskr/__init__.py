import pymongo
import sys
import os
from flask import Flask, current_app, g
from . import db_config
from . import nifty500
from . import hitTicker
from . import runtime_config
from . import screener
# from .whatsapp.messageClassifier import whatsappClassifier
from .whatsapp import whatsapp
from . import warrensden

# calls = {};
from . import fetchCommon

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        config_path = 'config.py'
        if('config_path' in os.environ):
            config_path = os.environ['config_path']; 
        app.config.from_pyfile(config_path, silent=False)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # a simple page that says hello
    app.config['calls']={'a':'132'}
    @app.route('/hello')
    def hello():
        print(current_app.config['calls']);
        current_app.config['calls']['b'] = '69'
        return 'Hello, World!'
    
    db_config.init_app(app)
    app.register_blueprint(nifty500.bp)
    app.register_blueprint(hitTicker.bp)
    app.register_blueprint(runtime_config.bp)
    app.register_blueprint(screener.bp)
    app.register_blueprint(whatsapp.bp)
    app.register_blueprint(warrensden.bp)
    app.register_blueprint(fetchCommon.bp)
    
    return app 