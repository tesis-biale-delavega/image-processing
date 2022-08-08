import os.path

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from services.OdmService import startup, stop_odm, odm_running, start_odm, odm_progress
from services.CoordsService import avg_coords
from services.ImageClassifier import classify_images
from services.IndexService import calculate_index, get_zone_above_threshold
from services.ProjectManagementService import list_projects, package_project, extract_project
import signal
import sys
from time import sleep
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
fig, ax = plt.subplots()
startup()


def signal_handler(signal, frame):
    stop_odm()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


@app.route('/odm-running')
def odm_is_running():
    return str(odm_running())


@app.post('/analysis')
def start_analysis():
    path = request.get_json()['path']
    name = request.get_json()['name']
    output_path = start_odm(path, name)
    return {
        "project_path": output_path,
        "orthophoto_path": os.path.join(output_path, 'rgb', 'odm_orthophoto', 'odm_orthophoto.png'),
        "coords": avg_coords(path, output_path)
    }


@app.post('/coords')
def coords():
    return avg_coords(request.get_json()['path'], request.get_json()['output_path'])


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
        fig, ax
    )
    return {
        'zone': response
    }


@app.get('/projects')
def get_projects():
    return {
        "projects": list_projects()
    }


@app.post('/compress')
def compress_project():
    return {
        "path": package_project(request.get_json()['path'])
    }


@app.post('/extract')
def extract():
    return extract_project(request.get_json()['path'])


if __name__ == '__main__':
    app.run(host="localhost", port=5001, debug=True)
