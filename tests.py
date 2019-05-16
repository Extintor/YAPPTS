import unittest
from server import bounds

class Test(unittest.TestCase):

    def setUp(self):
        pass

    def test_bounds(self):
        self.assertEqual(bounds(11, 2456, 7891), (-12053813.612459153, -134392195.17180088, -12034245.733218145,
                                                  -134372627.29203522))


if __name__ == '__main__':
    unittest.main()