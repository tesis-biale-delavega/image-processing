from flask import Flask, request, jsonify
from services.OdmService import startup, stop_odm, odm_running, start_odm, convert_single_channel_tif_to_png, unzip_file
from services.CoordsService import avg_coords
from services.ImageClassifier import classify_images
from services.IndexService import calculate_index, get_zone_above_threshold
import signal
import sys

app = Flask(__name__)
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
    start_odm(path)
    return 'ok'

