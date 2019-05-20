import unittest
import server
from unittest import mock
import psycopg2
from psycopg2 import pool
import asyncio
import tornado.testing


class Test(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()  # get ioloop

    def test_bounds(self):
        self.assertEqual(server.bounds(11, 2456, 7891), (-12053813.612459153, -134392195.17180088, -12034245.733218145,
                                                         -134372627.29203522))

    @mock.patch('psycopg2.pool.SimpleConnectionPool')
    def test_retrieve_tile(self, mock_pool):
        mock_pool.return_value.getconn.return_value.cursor.return_value.fetchall.return_value = \
            [(b'\x1a320a0474657374121d1202000018032215095aa63',),
             (b'\xf1a134631130a270f09280a121d0a14140f1a026331',)]
        mock_pool_connection = psycopg2.pool.SimpleConnectionPool(0, 0, 0, 0, 0, 0)

        expected = (b'\x1a320a0474657374121d1202000018032215095aa63'
                    b'\xf1a134631130a270f09280a121d0a14140f1a026331')

        result = server.retrieve_tile_from_db(mock_pool_connection, 11, 5, 25)
        self.assertEqual(result, expected)

    @mock.patch('server.retrieve_tile_from_db')
    def test_get_mvt(self, mock_retrieve):
        mock_retrieve.return_value = b'\x1a320a0474657374121d1202000018032215095aa63' \
                                     b'\xf1a134631130a270f09280a121d0a14140f1a026331'

        expected = (b'\x1a320a0474657374121d1202000018032215095aa63'
                    b'\xf1a134631130a270f09280a121d0a14140f1a026331')
        result = self.loop.run_until_complete(server.get_mvt(0, 11, 5, 25))
        self.assertEqual(result, expected)

    @mock.patch('psycopg2.pool.SimpleConnectionPool')
    def test_get_tile_init(self, mock_pool):
        mock_pool.return_value = "TEST"
        # result = server.get_tile(tornado.web.RequestHandler, mock_pool)
        # print(result.connection_pool)
        

if __name__ == '__main__':
    unittest.main()
