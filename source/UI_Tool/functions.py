from flaskapp import db
from flaskapp.user.routes import *
import requests
import json
import uuid


def save_image(data):
    collection = db.image_data

    try:
        for item in data:
            image = {
                "_id": uuid.uuid4().hex,
                "image_data": item.get("image"),
                "embedding": item.get("embedding"),
                "unverified_labels": item.get("labels"),
                "verified_labels": "",
                "incorrect_labels": "",
                "requiresVerification": "True"
            }

            collection.insert_one(image)

        return "Successfully saved image"
    except Exception as e:
        print(e)
        return "Error saving images to database."


def get_embeddings(face_data):
    """
    This function takes an array of dictionaries containing information about an image,
    and adds the image embeddings to each dictionary in the array.

    Args:
        face_data (list): list of dictionaries containing information about an image. 

    Returns:
        list: list of dictionaries with added image embeddings.
    """

    for item in face_data:
        response = requests.post("http://127.0.0.1:5002/get_embedding",
                                 headers={"Content-Type": "application/json"},
                                 data=json.dumps({"img": item["image"]}))

        if response.status_code == 200:
            data = response.json()

            if data.get("success") == "True":
                item["embedding"] = data.get("embedding")
            else:
                raise ValueError("Error generating embedding")
        else:
            raise ValueError("Error with embedding request")

    return face_data


def get_labels(face_data, endpoint):
    """
    Takes in an array of face data, where each element is a dictionary containing information about an image.
    Sends a request to the labelling api endpoint, passing the embedding for each image as the data.
    The endpoint returns a JSON object with the labels for the image.
    It then updates the face_data array with the labels for each image and returns the updated array. 
    """
    for item in face_data:

        response = requests.post(endpoint,
                                 headers={"Content-Type": "application/json"},
                                 data=json.dumps({"embedding": item["embedding"]}))

        if response.status_code == 200:
            data = response.json()
            if data.get("success") == "True":
                item["labels"] = data.get("labels")
            else:
                raise ValueError("Error retrieving labels")
        else:
            raise ValueError("Error with request")

    return face_data


def label_image(face_data, imageData):
    """
    Takes in face_data and imageData as input and sends a  request to "http://127.0.0.1:5009/label_image"
    with face_data and imageData in json format.
    Then returns the labelled_image and new_face_data.
    """

    response = requests.post("http://127.0.0.1:5003/draw_labels",
                             headers={"Content-Type": "application/json"},
                             data=json.dumps({"face_data": face_data, 'img': imageData}))

    # print("1")
    if response.status_code == 200:
        data = response.json()
        if data.get("success") == "True":
            # print("2")
            new_face_data = data.get("face_data")
            labelled_image = data.get("image_url")
            # print(new_face_data)
            # for item in new_face_data:
            #     print(item["name"])
        else:
            # print("3")
            raise ValueError("Error retrieving labels")
    else:
        # print("4")
        raise ValueError("Error with request")

    return labelled_image, new_face_data
