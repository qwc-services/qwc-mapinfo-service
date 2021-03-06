import os
import unittest
from urllib.parse import urlparse, parse_qs, urlencode

from flask import Response, json
from flask.testing import FlaskClient
from flask_jwt_extended import JWTManager, create_access_token

import server


class ApiTestCase(unittest.TestCase):
    """Test case for server API"""

    def setUp(self):
        os.environ["INFO_TABLE"] = "test_mapinfo"
        os.environ["INFO_GEOM_COL"] = "geometrie"
        os.environ["INFO_DISPLAY_COL"] = "gemeindename"
        os.environ["INFO_TITLE"] = "Gemeinde"

        server.app.testing = True
        self.app = FlaskClient(server.app, Response)
        JWTManager(server.app)

    def tearDown(self):
        pass

    def check_response(self, response, entries):
        response_data = json.loads(response.data)
        self.assertTrue(response_data)
        self.assertIn('results', response_data, 'Response has no results field')
        self.assertEqual(len(entries), len(response_data['results']), 'Response result count mismatch')

        for entry in response_data['results']:
            self.assertEqual(2, len(entry), 'Response result does not have two entries')
            self.assertEqual('Gemeinde', entry[0], 'Response result title mismatch')
            self.assertIn(entry[1], entries, 'Unexpected result')

    # submit query
    def test_mapinfo(self):
        response = self.app.get('/?' + urlencode({'pos': "%d,%d" % (3108, 206), 'crs': 'EPSG:2056'}))
        self.assertEqual(200, response.status_code, "Status code is not OK")
        self.check_response(response, ['Gemeinde 1'])

        response = self.app.get('/?' + urlencode({'pos': "%d,%d" % (15685,34), 'crs': 'EPSG:2056'}))
        self.assertEqual(200, response.status_code, "Status code is not OK")
        self.check_response(response, ['Gemeinde 2'])
