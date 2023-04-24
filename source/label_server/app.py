from flask import Flask, jsonify, request
import label
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


app = Flask(__name__)

# Neccessary to prevent CORS error being thrown.
# https://stackoverflow.com/questions/28461001/python-flask-cors-issue
CORS(app)

# https://dev.to/brightside/scheduling-tasks-using-apscheduler-in-django-2dbl#:~:text=Setting%20up%20APScheduler%3A%201%20Adding%20something_update.py%20to%20our,4%20Thank%20you%2C%20that%27s%20it%20for%20this%20tutorial.
scheduler = BackgroundScheduler()
# In a production environment, the scheduler would be set to run at a time of low usage (3-4am for example).
scheduler.add_job(label.update_data, 'interval',
                  minutes=5, start_date=datetime.now())
scheduler.start()

# Even though we have set up the scheduler, we need to call update_data() once to populate vi_index and
# vi_embeddings variable at start up.
label.update_data()

# x = label.vi_index.ntotal
# print(x)


@app.route('/', methods=['POST'])
def reset_index():
    label.update_data()
    return jsonify({'message': 'Data updated successfully'}), 204

# Clip method


@app.route('/label_method_1', methods=['POST'])
def label_clip_only():
    try:
        request_data = request.get_json()
        embedding = request_data.get('embedding')

        status, detected_labels = label.label_method_1(embedding)
        print("detected labels: " + str(detected_labels))

        if status == 'success':
            return jsonify({'success': 'True', 'labels': detected_labels})

        else:
            return jsonify({'success': 'False', 'msg': "Error in retrieving labels"})

    except Exception as e:
        print(e)
        return jsonify({'success': 'False', 'msg': "Internal server error."})

# origional (dont be wrong) method


@app.route('/label_method_2', methods=['POST'])
def get_labels_dont_be_wrong():
    try:
        request_data = request.get_json()
        embedding = request_data.get('embedding')

        status, detected_labels = label.label_method_2(embedding)
        print("detected labels: " + str(detected_labels))

        if status == 'success':
            return jsonify({'success': 'True', 'labels': detected_labels})

        else:
            return jsonify({'success': 'False', 'msg': "Error in retrieving labels"})

    except Exception as e:
        print(e)
        return jsonify({'success': 'False', 'msg': "Internal server error."})

# k nearest neighbour method


@app.route('/label_method_3', methods=['POST'])
def get_k_nearest_neighbour():
    try:
        request_data = request.get_json()
        embedding = request_data.get('embedding')

        status, detected_labels = label.label_method_3(embedding)
        print("detected labels: " + str(detected_labels))

        if status == 'success':
            return jsonify({'success': 'True', 'labels': detected_labels})

        else:
            return jsonify({'success': 'False', 'msg': "Error in retrieving labels"})

    except Exception as e:
        print(e)
        return jsonify({'success': 'False', 'msg': "Internal server error."})


@app.route('/label_method_4', methods=['POST'])
def label_method_4():
    try:
        request_data = request.get_json()
        embedding = request_data.get('embedding')

        status, detected_labels = label.label_method_4(embedding)
        print("detected labels: " + str(detected_labels))

        if status == 'success':
            return jsonify({'success': 'True', 'labels': detected_labels})

        else:
            return jsonify({'success': 'False', 'msg': "Error in retrieving labels"})

    except Exception as e:
        print(e)
        return jsonify({'success': 'False', 'msg': "Internal server error."})


@app.route("/draw_labels", methods=['POST'])
def draw_Labels():
    try:
        data = request.get_json()
        if not data:
            raise ValueError('No data received')

        # print(data['face_data'])

        # Create Image object from origional image
        raw_content = data["img"]

        if not raw_content:
            raise ValueError('No image data provided')

        decoded_string = base64.b64decode(raw_content[22:])
        image_bytes = BytesIO(decoded_string)
        image = Image.open(image_bytes)

        # create drawing context
        draw = ImageDraw.Draw(image)
        face_data = data['face_data']

        if not face_data:
            raise ValueError('No face data provided')

        count = 1
        # For each face in the image, get the labels and draw over original image
        for item in face_data:
            labels = item['labels']
            regions = item['regions']
            x, y, w, h = regions
            font = ImageFont.truetype('arial.ttf', 16)
            item['name'] = "face_"+str(count)

            # Draw Boxes
            # x,y = cordinates of the top left corner of the rectangle. w = width and h = height.
            draw.rectangle((x, y, x+w, y+h), outline=(255, 0, 0), width=2)

            # Draw labels
            # x,y = cordinates of the top left corner of the rectangle. w = width and h = height.
            # label_1
            # get label size. Returns tuple of (Width, height)
            label_Size = draw.textsize("Face "+str(count), font=font)
            print(label_Size)

            # get the centre points rectangle height and width.
            # x_centre = x+(w/2)
            # y_centre = y+(h/2)

            # Check of there is enough space above the image to tag the face
            if y-label_Size[1] > label_Size[1]:
                draw.text((x, y-25), "Face "+str(count),
                          font=font, fill=(255, 255, 255))
            # Check if there is enough space below the image to add the label
            elif y+h+label_Size[1] > label_Size[1]:
                draw.text((x, y+h+(label_Size[1]/2)), "Face "+str(count),
                          font=font, fill=(255, 255, 255))

            count = count + 1

            # draw.text((x-20, y+h+20), labels[1], font=font, fill=(255, 255, 255))
            # draw.text((x+w+20, y+h+20), labels[2], font=font, fill=(255, 255, 255))

            # draw.line((x-50, y+h+10, x, y), fill=(255, 255, 255), width=2)
            # draw.line((x+w+50, y+h+10, x+w, y), fill=(255, 255, 255), width=2)

        new_image_arr = BytesIO()
        image.save(new_image_arr, format='PNG')
        # image.show()
        new_encoded_image = base64.encodebytes(
            new_image_arr.getvalue()).decode('ascii)')

        new_image_arr.close()
        image.close()
        image_bytes.close()

        return jsonify({'success': 'True', 'image_url': new_encoded_image, 'face_data': face_data})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})

    except Exception as e:
        return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'})

    # guid = uuid.uuid4()

    # new_bytes = BytesIO()
    # image.save(new_bytes, 'PNG')

    # image.show()

    # filepath = "temp_data\\"+str(guid)+".jpg"
    # image_bytes = image.tobytes()

    # image_64 = base64.b64encode(image_bytes).decode("ascii")

    # newImage = "data:image/png;base64,"+image_64
    # with open(filepath, "wb") as f:
    #     f.write(image)

    # with open(filepath, 'rb') as f:
    #     image_bytes = f.read()

    # if os.path.exists(filepath):
    #     os.remove(filepath)
    #     print("file deleted")

    # return send_file(BytesIO(image_bytes), mimetype='image/png')

    # return json.dumps({"msg": "success", "image": newImage})

    # return Response(image_bytes, mimetype='image/png')


if __name__ == "__main__":
    # app.run(debug=True, port=5000)
    app.run(debug=True, port=5003)
