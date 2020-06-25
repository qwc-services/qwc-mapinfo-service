from io import BytesIO
import os
import re
import sys

from flask import Flask, request, jsonify
from flask_restx import Resource, fields, reqparse
import requests

from sqlalchemy.sql import text as sql_text

from qwc_services_core.api import Api
from qwc_services_core.api import CaseInsensitiveArgument
from qwc_services_core.app import app_nocache
from flask_jwt_extended import jwt_optional, get_jwt_identity
from qwc_services_core.jwt import jwt_manager
from qwc_services_core.database import DatabaseEngine
from qwc_services_core.tenant_handler import TenantHandler
from qwc_services_core.runtime_config import RuntimeConfig


# Flask application
app = Flask(__name__)
app_nocache(app)
api = Api(app, version='1.0', title='MapInfo service API',
          description="""API for QWC MapInfo service.

Additional information at a geographic position displayed with right mouse click on map.
          """,
          default_label='MapInfo operations', doc='/api/')
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

# disable verbose 404 error message
app.config['ERROR_404_HELP'] = False

auth = jwt_manager(app, api)

tenant_handler = TenantHandler(app.logger)

# request parser
mapinfo_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
mapinfo_parser.add_argument('pos', required=True)
mapinfo_parser.add_argument('crs', required=True)

db_engine = DatabaseEngine()

# routes
@api.route('/', endpoint='root')
class MapInfo(Resource):
    """MapInfo class

    Returns additional information at clicked map position.
    """

    @api.doc('mapinfo')
    @api.param('pos', 'Map position: x,y')
    @api.param('crs', 'CRS of the map position coordinates')
    @api.expect(mapinfo_parser)
    @jwt_optional
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        args = mapinfo_parser.parse_args()

        tenant = tenant_handler.tenant()
        config_handler = RuntimeConfig("mapinfo", app.logger)
        config = config_handler.tenant_config(tenant)

        db = db_engine.db_engine(config.get('db_url'))
        table = config.get('info_table')
        info_geom_col = config.get('info_geom_col')
        info_display_col = config.get('info_display_col')
        info_title = config.get('info_title')


        try:
            pos = args['pos'].split(',')
            pos = [float(pos[0]), float(pos[1])]
        except:
            return jsonify({"error": "Invalid position specified"})

        try:
            srid = int(re.match(r'epsg:(\d+)', args['crs'], re.IGNORECASE).group(1))
        except:
            return jsonify({"error": "Invalid projection specified"})

        conn = db.connect()

        sql = sql_text("""
            SELECT {display}
            FROM {table}
            WHERE ST_contains({table}.{geom}, ST_SetSRID(ST_Point(:x, :y), :srid))
            LIMIT 1;
        """.format(display=info_display_col, geom=info_geom_col, table=table))

        result = conn.execute(sql, x=pos[0], y=pos[1], srid=srid)
        info_result = []
        for row in result:
            info_result = [[info_title, row[info_display_col]]]

        conn.close()

        return jsonify({"results": info_result})


""" readyness probe endpoint """
@app.route("/ready", methods=['GET'])
def ready():
    return jsonify({"status": "OK"})


""" liveness probe endpoint """
@app.route("/healthz", methods=['GET'])
def healthz():
    return jsonify({"status": "OK"})


# local webserver
if __name__ == "__main__":
    from flask_cors import CORS
    CORS(app)
    app.run(host='localhost', port=5016, debug=True)
