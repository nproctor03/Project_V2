from flask import Flask, jsonify, request, session, redirect
from passlib.hash import pbkdf2_sha256
import uuid
from flaskapp import db


class User:

    def start_session(self, user):
        """_summary_
        Starts session when user logs in with valid data. Deletes user passeord and user id from session for security. 
        """
        del user['password']
        del user['_id']
        session['logged_in'] = True
        session['user'] = user

        # print(session)
        if user['admin'] == "true":
            session['isAdmin'] = True
        else:
            session['isAdmin'] = False

        return jsonify(user), 200

    # Performs user log in and starts session if credentials are correct.
    def login(self):
        """_summary_
        Retrieves user inputed password and username from request. Validates inputs and checks user details are correct. 
        If correct, creates a user session by calling start_session(). Else returns appropriate validation message. 
        """
        username = request.form.get('username')
        password = request.form.get('password')
        if len(username.strip()) < 1 or len(username.strip()) > 50:
            return jsonify({"error": "Username and Password must be between 1 and 50 characters."}), 401
        if len(password.strip()) < 1 or len(password.strip()) > 50:
            return jsonify({"error": "Username and Password must be between 1 and 50 characters."}), 401
        user = db.users.find_one({
            "name": username
        })

        if user and pbkdf2_sha256.verify(password, user['password']):
            return self.start_session(user)

        return jsonify({"error": "Invalid Login Credentials."}), 401

    # Creates and normal user.
    def create_user(self):
        """_summary_
        Validates form data and, if valid, creates a normal user. 
        """
        username = request.form.get('username')
        password = request.form.get('password')
        if len(username.strip()) < 1 or len(username.strip()) > 50:
            return jsonify({"error": "Username and Password must be between 1 and 50 characters."}), 401
        if len(password.strip()) < 1 or len(password.strip()) > 50:
            return jsonify({"error": "Username and Password must be between 1 and 50 characters."}), 401

        user = {
            "_id": uuid.uuid4().hex,
            "name": request.form.get('username'),
            "password": request.form.get('password'),
            "admin": "false"
        }

        if db.users.find_one({"name": user['name']}):
            return jsonify({"error": "Username already exists. Please choose another"}), 400

        user["password"] = pbkdf2_sha256.encrypt(user["password"])
        if db.users.insert_one(user):
            return jsonify("User successfully created"), 200

        return jsonify("Error Creating User"), 400

    # Creates and admin user.
    def create_admin_user(self):
        """_summary_
        Validates form data and, if valid, creates an admin user. 
        """
        username = request.form.get('username')
        password = request.form.get('password')

        if len(username.strip()) < 1 or len(username.strip()) > 50:
            return jsonify({"error": "Username and Password must be between 1 and 50 characters."}), 401
        if len(password.strip()) < 1 or len(password.strip()) > 50:
            return jsonify({"error": "Username andPassword must be between 1 and 50 characters."}), 401

        user = {
            "_id": uuid.uuid4().hex,
            "name": request.form.get('username'),
            "password": request.form.get('password'),
            "admin": "true"
        }

        if db.users.find_one({"name": user['name']}):
            return jsonify({"error": "Username already exists. Please choose another"}), 400
        # Encrypt the password.
        user["password"] = pbkdf2_sha256.encrypt(user["password"])
        if db.users.insert_one(user):
            return jsonify("Admin user successfully created"), 200

        return jsonify("Error Creating User"), 400

    def signout(self):
        """_summary_
        Destroys user session and navigates the user to the home page. 
        """
        session.clear()
        return redirect('/')
