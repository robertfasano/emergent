from flask import Blueprint
import json
from emergent.utilities import recommender

url_prefix = ''

def get_blueprint(network):
    lists = Blueprint('list', __name__)

    @lists.route('/models')
    def models():
        return json.dumps(recommender.list_classes('model'))

    @lists.route('/samplers')
    def samplers():
        return json.dumps(recommender.list_classes('sampler'))

    @lists.route('/servos')
    def servos():
        return json.dumps(recommender.list_classes('servo'))

    return lists
