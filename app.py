from flask import Flask
from services.OdmService import startup, stop_odm, odm_running
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
