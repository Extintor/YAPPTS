import unittest
import server
from unittest import mock
import psycopg2
from psycopg2 import pool


class Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_bounds(self):
        self.assertEqual(server.bounds(11, 2456, 7891), (-12053813.612459153, -134392195.17180088, -12034245.733218145,
                                                         -134372627.29203522))

    @mock.patch('psycopg2.pool.SimpleConnectionPool')
    def test_retrieve_tile(self, mock_pool):
        mock_pool.return_value.getconn.return_value.cursor.return_value.fetchall.return_value = \
            [(b'\x1a320a0474657374121d1202000018032215095aa63',),
             (b'\xf1a134631130a270f09280a121d0a14140f1a026331',)]
        mock_pool_connection = psycopg2.pool.SimpleConnectionPool(0, 0, 0, 0, 0, 0)

        query_result = (b'\x1a320a0474657374121d1202000018032215095aa63\xf1a134631130a270f09280a121d0a14140f1a026331')

        result = server.retrieve_tile_from_db(mock_pool_connection, 11, 5, 25)
        self.assertEqual(result, query_result)

if __name__ == '__main__':
    unittest.main()