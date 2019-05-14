import psycopg2
from psycopg2 import pool
import pyproj
import mercantile
import io
import os
import tornado.ioloop
import tornado.web
import errno


def bounds(zoom, x, y):
    in_proj = pyproj.Proj(init='epsg:4326')
    out_proj = pyproj.Proj(init='epsg:3857')
    lnglatbbox = mercantile.bounds(x, y, zoom)
    ws = (pyproj.transform(in_proj, out_proj, lnglatbbox[0],
                           lnglatbbox[1]))
    en = (pyproj.transform(in_proj, out_proj, lnglatbbox[2],
                           lnglatbbox[3]))
    return (ws[0], ws[1], en[0], en[1])


async def get_mvt(connection_pool, zoom,x,y):
    zoom = int(zoom)
    x = int(x)
    y = int(y)
    directory = str(zoom)+"/"+str(x)+"/"
    try:
        tile_file = open(directory+str(y)+".pbf", "rb")
        final_tile = tile_file.read()
        tile_file.close()
    except FileNotFoundError:
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
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        tile_file = open(directory + str(y) + ".pbf", "wb")
        tile_file.write(final_tile)
        tile_file.close()

    return final_tile


class GetTile(tornado.web.RequestHandler):
    def initialize(self, connection_pool):
        self.connection_pool = connection_pool

    async def get(self, zoom,x,y):
        self.set_header("Content-Type", "application/x-protobuf")
        self.set_header("Content-Disposition", "attachment")
        self.set_header("Access-Control-Allow-Origin", "*")
        response = await get_mvt(self.connection_pool, zoom, x, y)
        self.write(response)


if __name__ == "__main__":
    connection_pool = psycopg2.pool.\
                      SimpleConnectionPool(1, 20,
                                           user="mapas",
                                           password="tilemill",
                                           host="192.168.79.2",
                                           port="5432",
                                           database="mapes_db")
    if connection_pool:
        print("Connection pool created successfully")

    application = tornado.web.Application([
        (r"/tiles/([0-9]+)/([0-9]+)/([0-9]+).pbf", GetTile,
            dict(connection_pool=connection_pool))])
    print("YAPPTS started..")
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()