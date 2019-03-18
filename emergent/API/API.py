from flask import Flask, make_response, request, send_file
import numpy as np
import pickle
import pandas as pd
import json
import io
import uuid
import datetime
import matplotlib.pyplot as plt
from emergent.utilities import recommender, introspection
from emergent.utilities.containers import DataDict
from emergent.utilities.networking import get_address
from emergent.modules import ProcessHandler
import importlib, inspect

manager = ProcessHandler()

def serve(network, addr):
    app = Flask(__name__)

    blueprints=importlib.import_module('emergent.API.blueprints')
    for item in inspect.getmembers(blueprints, inspect.ismodule):
        blueprint = item[1].get_blueprint(network)
        app.register_blueprint(blueprint, url_prefix=item[1].url_prefix)

    @app.route("/")
    def hello():
        return "EMERGENT API"

    @app.route("/handshake", methods=['GET', 'POST'])
    def handshake():
        if request.method == 'POST':
            network.start_flask_socket_server()
        return 'connected'

    ''' Network endpoints '''
    @app.route('/state', methods=['GET', 'POST'])
    def state():
        if request.method == 'POST':
            state = request.get_json()
            network.actuate(state, send_over_p2p=False)
        return json.dumps(network.state())

    @app.route('/range', methods=['GET', 'POST'])
    def range():
        if request.method == 'POST':
            range = request.get_json()
            network.set_range(range)
        return json.dumps(network.range())


    app.run(host=addr, debug=False, threaded=True)
