from flask import Flask, request
import json
from emergent.utilities import recommender, introspection
from emergent.core import ProcessHandler
import importlib, inspect

manager = ProcessHandler()

def serve(network, addr, port):
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

    @app.route('/models/<model>/weights')
    def list_weights(model):
        model = recommender.get_class('model', model)
        files = []
        import os
        files = [x for x in os.listdir(os.getcwd()+'/'+network.path['data']) if model.extension in x]

        return json.dumps(files)

    app.run(host=addr, port=port, debug=False, threaded=True)
