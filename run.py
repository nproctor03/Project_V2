from flask import render_template, request, jsonify
from flaskapp import app, login_required, admin_required, db
from flaskapp.user.routes import *
import requests
import json
from functions import get_embeddings, get_labels, label_image, save_image


@app.route('/')
def render_home_page():
    return render_template('home.html')


@app.route('/analyser/')
def render_analyser_page():
    return render_template('faceAnalyser.html')


@app.route('/verify/')
@login_required
def render_verify_page():

    result = db.image_data.find_one({"requiresVerification": "True"})
    if result:
        # print(result)
        labels = result.get("unverified_labels")
        image_src = result.get("image_data")
        id = result.get("_id")
        # print(id)
        return render_template('verifyLabels.html', labels=labels, image_src=image_src, id=id)

    return render_template('verifyLabels.html')

    #  return render_template('verifyLabels.html', image = image, labels - labels)

    # return render_template('verifyLabels.html')


# https://www.w3schools.com/python/python_mongodb_update.asp
@app.route('/update_labels/', methods=["POST"])
def update_labels():

    # Need to convert form from Immutable Dict object to a normal dict to allow us to manipulate data. We pop the id value into its own
    # variable to make processing easier later on.
    form = request.form.to_dict()
    id = form.pop("_id", None)
    # print(id)

    verified_labels = list(form.values())

    # print(verified_labels)

    # get list of unverified labels so we can update incorrect labels.
    image_data = db.image_data.find_one({"_id": id})
    unverified_labels = image_data['unverified_labels']

    # remove items in verified labels from unverified labels using a list comprehesion
    # https://www.geeksforgeeks.org/python-remove-all-values-from-a-list-present-in-other-list/
    incorrect_labels = [
        i for i in unverified_labels if i not in verified_labels]

    # print("All labels: " + str(unverified_labels))
    # print("incorrect labels: " + str(incorrect_labels))

    filter = {'_id': id}
    newvalues = {"$set": {"unverified_labels": "", "verified_labels": verified_labels,
                          "incorrect_labels": incorrect_labels, "requiresVerification": "False"}}

    db.image_data.update_one(filter, newvalues)
    # print(id)

    return render_verify_page()


@app.route('/login/')
def render_login_page():
    return render_template("login.html")


@app.route('/createaccount/')
@admin_required
def render_create_account_page():
    return render_template("createUser.html")


@app.route('/processimage', methods=["POST"])
def process_image():
    req = request.get_json()
    try:
        if "img" not in req:
            return jsonify({"success": 'false', 'msg': 'No image found in request'})

        image_data = req["img"]

        endpoint = "http://127.0.0.1:5010/detect"
        headers = {"Content-Type": "application/json"}

        response = requests.post(endpoint, headers=headers,
                                 json={"img": image_data})

        if response.status_code != 200:
            return jsonify({"success": "false", 'msg': 'There was an error processing the image'})

        print("faces detected")
        data = response.json()

        # .get checks if "FaceDetected" exists in data. if it does it returns default value false.
        # If value of "FaceDeteced" != True, it returns an error message.
        if data.get("FaceDetected", "False") != "True":
            return jsonify({'success': 'True', 'FaceDetected': 'False'})

        # If faces were detected, get faces from response object.
        faces = data.get("faces")

        # loop through faces and create a dictionary item in face_data for each face.
        face_data = [{
            "image": face[0],
            "regions": face[1],
            "embedding": "",
            "labels": [],
            "name": ""
        }

            for face in faces]

        face_data = get_embeddings(face_data)
        print("embedding retrieved")
        face_data = get_labels(face_data)
        print("labels retrieved")
        labelled_image, complete_face_data = label_image(face_data, image_data)
        save_image(face_data)

        # print(complete_face_data)
        return jsonify({
            "success": 'True',
            'FaceDetected': 'True',
            'image_url': labelled_image,
            'face_data': complete_face_data
        })
    except (KeyError, ValueError) as e:
        print(e)
        return jsonify({'success': 'false', 'msg': 'There was an error processing the image.'})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
