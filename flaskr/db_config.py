import sqlite3

import click
import pymongo
from flask import current_app, g
import ssl
import certifi

def get_db():
    if 'db' not in g:
        g.db = pymongo.MongoClient(current_app.config['DATABASE_CONNECTION'], tlsCAFile=certifi.where())

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    get_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)