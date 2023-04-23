from flask import Flask, jsonify, request
from flask_cors import CORS
import base64
from PIL import Image
import cv2
import numpy as np
import clip
import torch

app = Flask(__name__)
CORS(app)

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-L/14", device=device, jit=True)


@app.route('/')
def index():
    return "Success"


@app.route('/get_embedding', methods=["POST"])
def process_image():
    try:
        req = request.get_json()

        if "img" not in req:
            return jsonify({'success': 'False', 'msg': 'No image found in request'}), 400

        raw_content = req["img"]
        decoded_string = base64.b64decode(raw_content)
        numpy_image = np.frombuffer(decoded_string, dtype=np.uint8)

        # Decode the image data from the numpy array
        img = cv2.imdecode(numpy_image, cv2.IMREAD_UNCHANGED)
        img = Image.fromarray(img)

        # Get embedding
        embedding = generate_embedding(img)
        return jsonify({'success': 'True', 'embedding': embedding.tolist()}), 200
    except Exception as e:
        print(e)
        return jsonify({'success': 'False', 'msg': 'Error Processing Image'}), 500


def generate_embedding(file):

    prepro = preprocess(file).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(prepro)
        # moves image features tensor from GPU to CPU if it is currently on GPU and casts as float.
        emb = image_features.to("cpu").float()
        # emb = image_features.cpu().detach().numpy().astype("float32")
    return emb


if __name__ == "__main__":
    app.run(debug=True, port=5002)
