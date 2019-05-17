import psycopg2
from psycopg2 import pool
import pyproj
import mercantile
import io
import os.path
import tornado.ioloop
import tornado.web
import configparser


def retrieve_tile_from_db(connection_pool, zoom, x, y):
    # Retrieve pbf tile info from PostgreSQL DB
    db_connection = connection_pool.getconn()
    cursor = db_connection.cursor()
    b_box = bounds(zoom, x, y)
    final_tile = b''
    cursor.execute("SELECT ST_AsMVT(q, 'test', 4096, 'geom') "
               "FROM (SELECT osm_id, ST_AsMVTGeom(geometry, "
               "ST_MakeBox2D(ST_Point({}, {}), "
               "ST_Point({}, {})), 4096, 256, true) AS geom "
               "FROM osm_new_buildings AS geom) "
               "AS q;".format(*b_box))
    for elem in cursor.fetchall():
        final_tile = final_tile + io.BytesIO(elem[0]).getvalue()
    cursor.close()
    connection_pool.putconn(db_connection)
    return final_tile

def bounds(zoom, x, y):
    # TODO Refactor into my own function
    in_proj = pyproj.Proj(init='epsg:4326')
    out_proj = pyproj.Proj(init='epsg:3857')
    lnglatbbox = mercantile.bounds(x, y, zoom)
    ws = (pyproj.transform(in_proj, out_proj, lnglatbbox[0],
                           lnglatbbox[1]))
    en = (pyproj.transform(in_proj, out_proj, lnglatbbox[2],
                           lnglatbbox[3]))

    return ws[0], ws[1], en[0], en[1]


async def get_mvt(connection_pool, zoom, x, y):
    zoom = int(zoom)
    x = int(x)
    y = int(y)
    # Get tile from DB
    final_tile = retrieve_tile_from_db(connection_pool, zoom, x, y)

    return final_tile


class get_tile(tornado.web.RequestHandler):
    def initialize(self, connection_pool):
        self.connection_pool = connection_pool

    async def get(self, zoom, x, y):
        self.set_header("Content-Type", "application/x-protobuf")
        self.set_header("Content-Disposition", "attachment")
        self.set_header("Access-Control-Allow-Origin", "*")
        response = await get_mvt(self.connection_pool,
                                 zoom, x, y)
        self.write(response)


if __name__ == "__main__":
    print("Starting YAPPTS...")

    # Parse all configuration information
    if not os.path.exists('yappts.ini'):
        raise FileNotFoundError("Configuration file not found")
    config = configparser.ConfigParser()
    config.read('yappts.ini')

    connection_pool = psycopg2.pool.SimpleConnectionPool(
                        config['POSTGRESQL']['minConnections'],
                        config['POSTGRESQL']['maxConnections'],
                        user=config['POSTGRESQL']['user'],
                        password=config['POSTGRESQL']['password'],
                        host=config['POSTGRESQL']['host'],
                        port=config['POSTGRESQL']['port'],
                        database=config['POSTGRESQL']['database'])

    if not connection_pool:
        raise ConnectionError("Could not connect with the PostgreSQL "
                              "database")


    application = tornado.web.Application(
                    [(r"/tiles/([0-9]+)/([0-9]+)/([0-9]+).pbf",
                     get_tile,
                     dict(connection_pool=connection_pool))])

    print("YAPPTS started...")
    server = tornado.httpserver.HTTPServer(application)
    server.listen(8888)
    server.start(1)
    tornado.ioloop.IOLoop.current().start()
