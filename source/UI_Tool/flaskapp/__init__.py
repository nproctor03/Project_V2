from flask import Flask, session, redirect, session, flash
from functools import wraps
from functools import wraps
import pymongo
import os

# This was originaly run.py, however a circular reference was being created between run.py and the User module.
# Users imports the db object from flaskapp. However, VS code was autoformatting the imports so that the user module
# was being imported before the db was instantiated. Therefore instantiate the db here and import flaskapp and users into
# run.py which solved the issue.

# db config
client = pymongo.MongoClient('localhost', 27017)
db = client.images

app = Flask(__name__)
app.secret_key = "b'W~\x9d\xe9\x13}2Ou\x1f\xdd\x9ct\x1d\xfc+'"

# decorators


def login_required(f):
    """_summary_
    Decorator which requires that a user be logged in to access the page
    """
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Login Required.")
            return redirect('/')
    return wrap


def admin_required(f):
    """_summary_
    Decorator which requires that a user be an admin user to access the page. 
    """
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session and session['isAdmin'] == True:
            return f(*args, **kwargs)
        else:
            return redirect('/')
    return wrap
