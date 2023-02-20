from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


app = Flask(__name__)
CORS(app)


@app.route("/label_image", methods=['POST'])
def label_Image():
    data = request.get_json()

    # Create Image object from origional image
    raw_content = data["img"]
    decoded_string = base64.b64decode(raw_content[22:])
    image_bytes = BytesIO(decoded_string)
    image = Image.open(image_bytes)

    # create drawing context
    draw = ImageDraw.Draw(image)

    face_data = data['face_data']
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

    #guid = uuid.uuid4()

    # new_bytes = BytesIO()
    # image.save(new_bytes, 'PNG')

    # image.show()

    #filepath = "temp_data\\"+str(guid)+".jpg"
    #image_bytes = image.tobytes()

    #image_64 = base64.b64encode(image_bytes).decode("ascii")

    #newImage = "data:image/png;base64,"+image_64
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


# def text(output_path):
#     image = Image.new("RGB", (200, 200), "green")
#     draw = ImageDraw.Draw(image)
#     draw.text((10, 10), "Hello from")
#     draw.text((10, 25), "Pillow",)
#     image.save(output_path)

if __name__ == "__main__":
    app.run(debug=True, port=5009)
