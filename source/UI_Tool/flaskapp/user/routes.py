from flask import Flask, render_template
from flaskapp import app
from flaskapp.user.models import User


@app.route('/user/login', methods=['POST'])
def login():
    return User().login()


@app.route('/user/create_admin', methods=['POST'])
def create_admin():
    return User().create_admin_user()


@app.route('/user/create_user', methods=['POST'])
def create_user():
    return User().create_user()


@app.route('/user/signout')
def signout():
    return User().signout()
