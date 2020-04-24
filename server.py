from io import BytesIO
import os
import re
import sys

from flask import Flask, request, jsonify
from flask_restplus import Resource, fields, reqparse
import requests

from sqlalchemy.sql import text as sql_text

# add parent dir to path, so shared modules can be imported
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(1, path)

from service_lib.api import Api  # noqa: E402
from service_lib.api import CaseInsensitiveArgument  # noqa: E402
from service_lib.app import app_nocache  # noqa: E402
from service_lib.auth import auth_manager, optional_auth, get_auth_user  # noqa: E402
from service_lib.database import DatabaseEngine  # noqa: E402

# Flask application
app = Flask(__name__)
app_nocache(app)
api = Api(app, version='1.0', title='MapInfo service API',
          description="""API for SO!MAP MapInfo service.

Additional information at a geographic position displayed with right mouse click on map.
          """,
          default_label='MapInfo operations', doc='/api/')
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

# disable verbose 404 error message
app.config['ERROR_404_HELP'] = False

auth = auth_manager(app, api)

# request parser
mapinfo_parser = reqparse.RequestParser(argument_class=CaseInsensitiveArgument)
mapinfo_parser.add_argument('pos', required=True)
mapinfo_parser.add_argument('crs', required=True)

db_engine = DatabaseEngine()
geo_db = db_engine.geo_db()

# routes
@api.route('/', endpoint='root')
class MapInfo(Resource):
    """MapInfo class

    Returns additional information at clicked map position.
    """

    def __init__(self, api):
        Resource.__init__(self, api)

        self.table = os.getenv("INFO_TABLE", "agi_hoheitsgrenzen_pub.hoheitsgrenzen_gemeindegrenze")
        self.geometryColumn = os.getenv("INFO_GEOM_COL", "geometrie")
        self.displayColumn = os.getenv("INFO_DISPLAY_COL", "gemeindename")
        self.resultTitle = os.getenv("INFO_TITLE", "Gemeinde")

    @api.doc('mapinfo')
    @api.param('pos', 'Map position: x,y')
    @api.param('crs', 'CRS of the map position coordinates')
    @api.expect(mapinfo_parser)
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        args = mapinfo_parser.parse_args()

        try:
            pos = args['pos'].split(',')
            pos = [float(pos[0]), float(pos[1])]
        except:
            return jsonify({"error": "Invalid position specified"})

        try:
            srid = int(re.match(r'epsg:(\d+)', args['crs'], re.IGNORECASE).group(1))
        except:
            return jsonify({"error": "Invalid projection specified"})

        conn = geo_db.connect()

        sql = sql_text("""
            SELECT {display}
            FROM {table}
            WHERE ST_contains({table}.{geom}, ST_SetSRID(ST_Point(:x, :y), :srid))
            LIMIT 1;
        """.format(display=self.displayColumn, geom=self.geometryColumn, table=self.table))

        result = conn.execute(sql, x=pos[0], y=pos[1], srid=srid)
        info_result = []
        for row in result:
            info_result = [[self.resultTitle, row[self.displayColumn]]]

        conn.close()

        return jsonify({"results": info_result})


# local webserver
if __name__ == '__main__':
    print("Starting MapInfo service...")
    app.run(host='localhost', port=5016, debug=True)
