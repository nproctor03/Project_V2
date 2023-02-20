from flask import Flask, session, redirect, session, flash
from functools import wraps
from functools import wraps
import pymongo
import os


# db config
client = pymongo.MongoClient('localhost', 27017)
db = client.images

# https://stackoverflow.com/questions/21765692/flask-render-template-with-path
app = Flask(__name__)
app.secret_key = "b'W~\x9d\xe9\x13}2Ou\x1f\xdd\x9ct\x1d\xfc+'"


# decorators
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Login Required.")
            return redirect('/')
    return wrap


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session and session['isAdmin'] == True:
            return f(*args, **kwargs)
        else:
            return redirect('/')
    return wrap
