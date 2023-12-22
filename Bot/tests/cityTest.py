import unittest
from Bot.tools.tools import city


class CityTest(unittest.TestCase):
    def test_Severodvinsk(self):
        lat, lon = city('Северодвинск')
        self.assertEqual(lat, 64.563385)
        self.assertEqual(lon, 39.823769)

    def test_Arkhangelsk(self):
        lat, lon = city('Arkhangelsk')
        self.assertEqual(lat, 64.543022)
        self.assertEqual(lon, 40.537121)


if __name__ == '__main__':
    unittest.main()