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
from qwc_services_core.auth import auth_manager, optional_auth
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

auth = auth_manager(app, api)

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
    @optional_auth
    def get(self):
        """Submit query

        Returns additional information at clicked map position.
        """
        args = mapinfo_parser.parse_args()

        tenant = tenant_handler.tenant()
        config_handler = RuntimeConfig("mapinfo", app.logger)
        config = config_handler.tenant_config(tenant)

        try:
            pos = args['pos'].split(',')
            pos = [float(pos[0]), float(pos[1])]
        except:
            return jsonify({"error": "Invalid position specified"})

        try:
            srid = int(re.match(r'epsg:(\d+)', args['crs'], re.IGNORECASE).group(1))
        except:
            return jsonify({"error": "Invalid projection specified"})

        info_result = []

        queries = config.get('queries') or [config]

        for config in queries:
            result = self.__process_query(config, pos, srid)
            if result:
                info_result.extend(result)

        return jsonify({"results": info_result})

    def __process_query(self, config, pos, srid):
        info_title = config.get('info_title')
        if config.get('info_sql') is not None:
             sql = sql_text(config.get('info_sql'))
        else:
            schema, table = ("public." + config.get('info_table')).split(".")[-2:]
            info_geom_col = config.get('info_geom_col')
            info_display_col = config.get('info_display_col')
            info_where = config.get('info_where')

            extra_where = ""
            if info_where is not None:
                extra_where = " AND (" + info_where + ")"

            sql = sql_text("""
                SELECT {display}
                FROM {schema}.{table}
                WHERE ST_contains({schema}.{table}.{geom}, ST_Transform(ST_SetSRID(ST_Point(:x, :y), :srid), Find_SRID('{schema}', '{table}', '{geom}'))){extra_where}
                LIMIT 1;
            """.format(display=info_display_col, geom=info_geom_col, schema=schema, table=table, extra_where=extra_where))

        db_url = config.get('db_url')
        db = db_engine.db_engine(db_url)
        with db.connect() as conn:
            params = {"x": pos[0], "y": pos[1], "srid": srid}
            app.logger.debug(f"info query: {sql}")
            app.logger.debug(f"params: {params}")

            try:
                result = conn.execute(sql, params).mappings()
            except:
                return None
            row = result.fetchone()
            if row is None:
                return_value = None
            elif config.get('info_sql') is not None:
                if not isinstance(info_title, list):
                    info_title = [info_title]
                return_value = [list(t) for t in zip(info_title, row.values())]
            else:
                return_value = [[info_title, row[info_display_col]]]

        return return_value


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
