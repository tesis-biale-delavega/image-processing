from flask import Flask, request, jsonify, Response
from services.OdmService import startup, stop_odm, odm_running, start_odm, odm_progress
from services.ImageClassifier import classify_images
from services.IndexService import calculate_index, get_zone_above_threshold
import signal
import sys
from time import sleep
import matplotlib.pyplot as plt


app = Flask(__name__)
fig, ax = plt.subplots()
startup()


def signal_handler(signal, frame):
    stop_odm()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


@app.route('/odm-running')
def odm_running():
    return str(odm_running())


@app.post('/analysis')
def start_analysis():
    path = request.get_json()['path']
    name = request.get_json()['name']
    start_odm(path, name)
    return 'ok'


@app.get('/progress')
def progress():
    def stream():
        while True:
            res, msg = odm_progress()
            if res is not None:
                yield str(res)
            else:
                yield '{\'error\':' + msg + '}'
            sleep(5)

    return Response(stream(), mimetype='application/json')


@app.route('/classify')
def classify():
    path = request.get_json()['path']
    return jsonify(classify_images(path))


@app.post('/index')
def index():
    json = request.get_json()
    response = calculate_index(
        json['project_path'],
        json['indexes'],
        json['custom_indexes'], fig, ax)
    return response


@app.get('/threshold')
def values_above_threshold():
    response = get_zone_above_threshold(
        request.get_json()['path'],
        request.get_json()['threshold_max'],
        request.get_json()['threshold_min'],
        request.get_json()['out'],
        fig, ax
    )
    return {
        'zone': response
    }

