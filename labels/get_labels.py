from flask import Flask, jsonify, request
import label
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


app = Flask(__name__)
CORS(app)

app.secret_key = "b'8{\x05\xfbFv'\x08t\x80\xe6\xc6\xdc\xad\xbay\x03ly\xeb\xad\xaa,t'"


@app.route('/')
def home():
    return "success"


@app.route('/get_labels', methods=['POST'])
def get_labels():
    try:
        request_data = request.get_json()
        embedding = request_data.get('embedding')

        status, detected_labels = label.label_image(embedding)

        if status == 'success':
            return jsonify({'success': 'True', 'labels': detected_labels})

        else:
            return jsonify({'success': 'False', 'msg': "Error in retrieving labels"})

    except Exception as e:
        print(e)
        return jsonify({'success': 'False', 'msg': "Internal server error."})


# print("Global: "+str(vi_index.ntotal))
# print("Global: "+str(vi_embeddings))
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


if __name__ == "__main__":
    app.run(debug=True, port=5003)
