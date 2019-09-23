from flask import Blueprint
from flask_restful import Api

from app.resources import KeyValuePairListResource, KeyValuePairResource

# Blueprint
api_bp = Blueprint('api/v1/', __name__)
api = Api(api_bp)

# Routes
api.add_resource(KeyValuePairListResource, '/keys/')
api.add_resource(KeyValuePairResource, '/keys/<string:key>')
