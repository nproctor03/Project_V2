from flask import render_template, request, jsonify
from flaskapp import app, login_required, admin_required, db
from flaskapp.user.routes import *
import requests
from functions import get_embeddings, get_labels, label_image, save_image


@app.route('/')
def render_home_page():
    """_summary_

    Returns:
        Renders the home.html webpage. 
    """
    return render_template('home.html')


@app.route('/analyser/')
def render_analyser_page():
    """_summary_

    Returns:
        Renders the faceAnalyser.html webpage. 
    """
    return render_template('faceAnalyser.html')


@app.route('/verify/')
@login_required
def render_verify_page():
    """_summary_

    This function is called when a request is made to the /verify/ endpoint. It queries the image database 
    and checks if an image exists in the database that requires verification. If an image exists, it retrieves 
    the unverified labels and the image data from the database and returns them as parameters to the verifyLabels.html
    template. If there is no image that requires verification, the template is returned without any parameters.

    Returns:
        Renders the verifyLabels.html webpage. 
    """
    result = db.image_data.find_one({"requiresVerification": "True"})
    if result:
        # print(result)
        labels = result.get("unverified_labels")
        image_src = result.get("image_data")
        id = result.get("_id")
        # print(id)
        return render_template('verifyLabels.html', labels=labels, image_src=image_src, id=id)

    return render_template('verifyLabels.html')

# https://www.w3schools.com/python/python_mongodb_update.asp


@app.route('/update_labels/', methods=["POST"])
def update_labels():
    """_summary_
    This function is called when a POST request is made to the '/update_labels/' endpoint. The function receives and 
    processes the form data sent in the request, and updates the relevant record in the image database. 

    """
    # Need to convert form from Immutable Dict object to a normal dict to allow us to manipulate data.
    form = request.form.to_dict()
    id = form.pop("_id", None)
    user_added_labels = form.pop("user-added-labels")
    user_added_labels = user_added_labels.split(",")
    user_added_labels.pop(-1)
    # Need to pop off the input value to prevent it being added. This is incase the user has
    # entered a label into the input but not clicked on submit.
    _ = form.pop("user-labels")
    # print(id)
    # print(form)
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
                          "incorrect_labels": incorrect_labels, "requiresVerification": "False", "UserAddedLabels": user_added_labels}}

    db.image_data.update_one(filter, newvalues)
    # print(id)
    return render_verify_page()


@app.route('/login/')
def render_login_page():
    """_summary_
        Renders the login.html webpage. 
    """
    return render_template("login.html")


@app.route('/createaccount/')
@admin_required
def render_create_account_page():
    """_summary_
        Renders the createUser.html webpage. Can only be accessed by an Admin user. 
    """
    return render_template("createUser.html")


@app.route('/processimage', methods=["POST"])
def process_image():
    """_summary_
    This function is called when a POST request is made to the /processimage endpoint. It retrieves the image data from the 
    request and sends the image to the Face Detection server. If the face detection server detects faces, it then sends each 
    individual face image to the embedding API and the labelling API to label the image and returns the labels attached. If
    no face is detected, returns "No Face Detected" in response. 
    """
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

        # print("faces detected")
        data = response.json()

        # .get checks if "FaceDetected" exists in data. if it does it returns default value false.
        # If value of "FaceDeteced" != True, it returns an error message.
        if data.get("FaceDetected", "False") != "True":
            # print("No faces detected")
            return jsonify({'success': 'True', 'FaceDetected': 'False'})

        # If faces were detected, get faces from response object.
        # print("Faces detected")
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

        # Get labelling method
        method = req["method"]
        if method == "method_1":
            label_endpoint = "http://127.0.0.1:5003/label_method_1"
            print("method 1")
        elif method == "method_2":
            label_endpoint = "http://127.0.0.1:5003/label_method_2"
            print("method 2")
        elif method == "method_3":
            label_endpoint = "http://127.0.0.1:5003/label_method_3"
            print("method 3")

        face_data = get_embeddings(face_data)
        # print("embedding retrieved")
        face_data = get_labels(face_data, label_endpoint)
        # print("labels retrieved")
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
