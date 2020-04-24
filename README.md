MapInfo service
===============

Additional information at a geographic position displayed with right mouse click on map.


Dependencies
------------

* Permission service (`PERMISSION_SERVICE_URL`)


Configuration
-------------

Environment variables:

| Variable            | Description                  | Default value                                          |
|---------------------|------------------------------|--------------------------------------------------------|
| `INFO_TABLE`        | Table to use                 | `agi_hoheitsgrenzen_pub.hoheitsgrenzen_gemeindegrenze` |
| `INFO_GEOM_COL`     | Geometry column in table     | `geometrie`                                            |
| `INFO_DISPLAY_COL`  | Display text column in table | `gemeindename`                                         |
| `INFO_TITLE`        | Display title                | `gemeinde`                                             |


Usage/Development
-----------------

API documentation:

    http://localhost:5016/api/

Testing
-------

See `../testing/README.md`.
