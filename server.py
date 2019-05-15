import psycopg2
from psycopg2 import pool
import pyproj
import mercantile
import io
import os.path
import tornado.ioloop
import tornado.web
import redis
import configparser
import errno


async def save_to_cache(redis_conn, tile_id, directory, name,  tile):
    redis_conn.set(tile_id, directory+name)
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    tile_file = open(directory + name + ".pbf", "wb")
    tile_file.write(tile)
    tile_file.close()


def retrieve_file_from_disk(location):
    tile_file = open(location + ".pbf", "rb")
    final_tile = tile_file.read()
    tile_file.close()

    return final_tile


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


async def get_mvt(connection_pool, redis_pool, zoom, x, y):
    zoom = int(zoom)
    x = int(x)
    y = int(y)
    tile_id = str(zoom) + str(x) + str(y)

    # Check if file location is in Redis
    r = redis.Redis(connection_pool=redis_pool)
    redis_loc = r.get(tile_id)
    try:
        # Get tile from disk
        final_tile = retrieve_file_from_disk(str(redis_loc)[2:-1])
    except FileNotFoundError:
        # Get tile from DB
        final_tile = retrieve_tile_from_db(connection_pool, zoom, x, y)
        await save_to_cache(r,
                            tile_id,
                            str(zoom) + "/" + str(x) + "/",
                            str(y),
                            final_tile)


    return final_tile


class GetTile(tornado.web.RequestHandler):
    def initialize(self, connection_pool, redis_pool):
        self.connection_pool = connection_pool
        self.redis_pool = redis_pool

    async def get(self, zoom, x, y):
        self.set_header("Content-Type", "application/x-protobuf")
        self.set_header("Content-Disposition", "attachment")
        self.set_header("Access-Control-Allow-Origin", "*")
        response = await get_mvt(self.connection_pool, self.redis_pool,
                                 zoom, x, y)
        self.write(response)


if __name__ == "__main__":
    print("Starting YAPPTS...")

    # Parse all configuration information
    if not os.path.exists('yappts.ini'):
        raise FileNotFoundError("Configuration file not found")
    config = configparser.ConfigParser()
    config.read('yappts.ini')

    connection_pool = psycopg2.pool.ThreadedConnectionPool(
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
    # TODO Fix caching, slower than generating tiles?
    redis_pool = redis.ConnectionPool(
        host='redis-13882.c135.eu-central-1-1.ec2.cloud.redislabs.com',
        port=13882,
        password='dbWpteeJL36hUyfpv0Z1XoIBxHLtxJ7e')

    application = tornado.web.Application(
                    [(r"/tiles/([0-9]+)/([0-9]+)/([0-9]+).pbf",
                        GetTile,
                        dict(connection_pool=connection_pool,
                             redis_pool=redis_pool))])

    print("YAPPTS started...")
    server = tornado.httpserver.HTTPServer(application)
    server.listen(8888)
    server.start(0)  # Forks multiple sub-processes
    tornado.ioloop.IOLoop.current().start()
    tornado.ioloop.IOLoop.set_blocking_log_threshold(0.05)
