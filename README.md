[![](https://github.com/qwc-services/qwc-mapinfo-service/workflows/build/badge.svg)](https://github.com/qwc-services/qwc-mapinfo-service/actions)
[![docker](https://img.shields.io/docker/v/sourcepole/qwc-mapinfo-service?label=Docker%20image&sort=semver)](https://hub.docker.com/r/sourcepole/qwc-mapinfo-service)

QWC MapInfo Service
===================

Additional information at a geographic position displayed with right mouse click on map.


Configuration
-------------

The static config files are stored as JSON files in `$CONFIG_PATH` with subdirectories for each tenant,
e.g. `$CONFIG_PATH/default/*.json`. The default tenant name is `default`.

### MapInfo Service config

* [JSON schema](schemas/qwc-mapinfo-service.json)
* File location: `$CONFIG_PATH/<tenant>/mapinfoConfig.json`

Examples:

```json
{
  "$schema": "https://raw.githubusercontent.com/qwc-services/qwc-mapinfo-service/master/schemas/qwc-mapinfo-service.json",
  "service": "mapinfo",
  "config": {
    "db_url": "postgresql:///?service=qwc_geodb",
    "info_table": "qwc_geodb.ne_10m_admin_0_countries",
    "info_geom_col": "wkb_geometry",
    "info_display_col": "name",
    "info_title": "Country",
    "info_id": "country"
  }
}
```

```json
{
  "$schema": "https://raw.githubusercontent.com/qwc-services/qwc-mapinfo-service/master/schemas/qwc-mapinfo-service.json",
  "service": "mapinfo",
  "config": {
    "db_url": "postgresql:///?service=qwc_geodb",
    "info_table": "qwc_geodb.ne_10m_admin_0_countries",
    "info_geom_col": "wkb_geometry",
    "info_display_col": "name",
    "info_title": "Country",
    "info_id": "country",
    "info_where": "pop_est > 600000"
  }
}
```

```json
{
  "$schema": "https://raw.githubusercontent.com/qwc-services/qwc-mapinfo-service/master/schemas/qwc-mapinfo-service.json",
  "service": "mapinfo",
  "config": {
    "queries": [
      {
        "db_url": "postgresql:///?service=qwc_geodb",
        "info_table": "qwc_geodb.ne_10m_admin_0_countries",
        "info_geom_col": "wkb_geometry",
        "info_display_col": "name",
        "info_title": "Country",
        "info_id": "country"
      },
      {
        "db_url": "postgresql:///?service=qwc_geodb",
        "info_sql": "SELECT type FROM qwc_geodb.ne_10m_admin_0_countries WHERE ST_contains(wkb_geometry, ST_SetSRID(ST_Point(:x, :y), :srid)) LIMIT 1",
        "info_title": "Type",
        "info_id": "type"
      },
      {
        "db_url": "postgresql:///?service=qwc_geodb",
        "info_sql": "SELECT abbrev, postal, subregion FROM qwc_geodb.ne_10m_admin_0_countries WHERE ST_contains(wkb_geometry, ST_SetSRID(ST_Point(:x, :y), :srid)) LIMIT 1",
        "info_title": ["Abbreviation", "Postal Code", "Subregion"],
        "info_id": "region"
      }
    ]
  }
}
```


### Environment variables

Config options in the config file can be overridden by equivalent uppercase environment variables.

| Variable            | Description                  |
|---------------------|------------------------------|
| `INFO_TABLE`        | Table to use                 |
| `INFO_GEOM_COL`     | Geometry column in table     |
| `INFO_DISPLAY_COL`  | Display text column in table |
| `INFO_TITLE`        | Display title                |


### Permissions


* [JSON schema](https://github.com/qwc-services/qwc-services-core/blob/master/schemas/qwc-services-permissions.json)
* File location: `$CONFIG_PATH/<tenant>/permissions.json`

Example:
```json
{
  "$schema": "https://raw.githubusercontent.com/qwc-services/qwc-services-core/master/schemas/qwc-services-permissions.json",
  "users": [
    {
      "name": "demo",
      "groups": ["demo"],
      "roles": []
    }
  ],
  "groups": [
    {
      "name": "demo",
      "roles": ["demo"]
    }
  ],
  "roles": [
    {
      "role": "public",
      "permissions": {
        "mapinfo_query": [
          "country",
          "type",
          "region"
        ]
      }
    },
    {
      "role": "demo",
      "permissions": {
        "mapinfo_query": []
      }
    }
  ]
}
```



Usage
-----

Run as

    python src/server.py

API documentation:

    http://localhost:5016/api/

Docker usage
------------

See sample [docker-compose.yml](https://github.com/qwc-services/qwc-docker/blob/master/docker-compose-example.yml) of [qwc-docker](https://github.com/qwc-services/qwc-docker).


Development
-----------

Install dependencies and run service:

    uv run src/server.py

With config path:

    CONFIG_PATH=/PATH/TO/CONFIGS/ uv run src/server.py

Testing
-------

Run all tests:

    python test.py
