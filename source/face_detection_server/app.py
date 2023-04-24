from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from deepface import DeepFace
from deepface.detectors import FaceDetector
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import base64

app = Flask(__name__)

# Neccessary to prevent CORS error being thrown.
# https://stackoverflow.com/questions/28461001/python-flask-cors-issue
CORS(app)


@app.route('/')
def index():
    return "Success"


@app.route('/detect', methods=["POST"])
def detect():
    req = request.get_json()
    if "img" not in req:
        return make_response(jsonify(success="False", error='No Image Detected'), 400)

    try:
        # Get base64 encoded string from request object
        raw_content = req["img"]
        # decode the base 64 string
        # https://stackoverflow.com/questions/33754935/read-a-base-64-encoded-image-from-memory-using-opencv-python-library
        decoded_string = base64.b64decode(raw_content[22:])
        # create array of decoded string
        numpy_image = np.frombuffer(decoded_string, dtype=np.uint8)
        # convert array to image. Processing the image this way prevents us from having to temporarily save the image to disk.
        img = cv2.imdecode(numpy_image, cv2.IMREAD_COLOR)

        # build face detector model
        # https://github.com/serengil/deepface/blob/master/deepface/detectors/FaceDetector.py
        detector_backend = "opencv"
        face_detector = FaceDetector.build_model(detector_backend)
        faces = FaceDetector.detect_faces(face_detector, detector_backend, img)

        if len(faces) > 0:
            data = []
            # process each face to send in response.
            for face in faces:
                # The next 3 lines of code are important as they allow the image to be saved and sent without temporarily saving to disk.
                # Image is returned as a np array. So need to format in order for it to be sent in response.
                image = Image.fromarray(face[0])
                image_arr = BytesIO()
                image.save(image_arr, format='PNG')
                encoded_image = base64.encodebytes(
                    image_arr.getvalue()).decode('ascii')
                regions = face[1]

                # need to convert regions from int 32 to int to allow them to be converted to json. Was getting an error with int32.
                for i, x in enumerate(regions):
                    regions[i] = int(x)

                values = [encoded_image, regions]
                data.append(values)

                # close the image object.
                image.close()
                image_arr.close()

            # # close the image object.
            # image.close()
            # image_arr.close()

            return make_response(jsonify(success='True', FaceDetected='True', faces=data), 200)
        else:
            return make_response(jsonify(success='True', FaceDetected='False'), 200)

    except Exception as e:
        print(e)
        return make_response(jsonify(success='False', error='Error processing image'), 400)


if __name__ == "__main__":
    app.run(debug=True, port=5010)
