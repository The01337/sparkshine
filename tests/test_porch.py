import datetime
import unittest
import json

import porch


class PorchTest(unittest.TestCase):
    def test_getdaylight(self):
        with open('./settings.json') as f:
            settings = json.load(f)
        start, end = porch.get_daylight(latitude=settings['latitude'], longitude=settings['longitude'])
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)

    def test_parsedate(self):
        self.assertIsNotNone(porch.parse_date('2018-05-15T01:31:14+00:00'))
        self.assertIsNotNone(porch.parse_date('1018-02-12T21:31:14+00:00'))
        self.assertIsNotNone(porch.parse_date('2018-05-15T23:31:14+00:00'))

        self.assertRaises(ValueError, porch.parse_date, '2018-05-35T01:31:14+00:00')
        self.assertRaises(ValueError, porch.parse_date, '2018-02-30T01:31:14+00:00')
        self.assertRaises(ValueError, porch.parse_date, '2018-05-15 T 01:31:14+00:00')
        self.assertRaises(ValueError, porch.parse_date, '2018-05-15T31:31:14+00:00')
        self.assertRaises(ValueError, porch.parse_date, '2018-05-15T01:71:14+00:00')
        self.assertRaises(ValueError, porch.parse_date, '2018-05-15T01:31:14+01:00')
        self.assertRaises(ValueError, porch.parse_date, '2018-05-15T01:31:14+things')

    def test_checkdarkness(self):
        # We are not considering to be in locations where arctic days/nights are happening
        with open('./settings.json') as f:
            settings = json.load(f)
        now = datetime.datetime.utcnow()
        self.assertEqual(
            porch.check_darkness(now.replace(hour=0), latitude=settings['latitude'], longitude=settings['longitude']),
            # Should be dark minutes AFTER midnight
            True
        )
        self.assertEqual(
            porch.check_darkness(now.replace(hour=13), latitude=settings['latitude'], longitude=settings['longitude']),
            # Should NOT be dark minutes after noon
            False
        )
        self.assertEqual(
            porch.check_darkness(now.replace(hour=23), latitude=settings['latitude'], longitude=settings['longitude']),
            # Should be dark minutes BEFORE midnight
            True
        )

    def test_readleases(self):
        with open('./settings.json') as f:
            settings = json.load(f)
        output = porch.read_leases('./dhcpd.leases.bak', settings['macs'])
        self.assertEqual(
            output, [
                {'mac': settings['macs'][0], 'ltt': datetime.datetime(2018, 5, 15, 5, 39, 42), 'ip': '192.168.0.10'},
                {'mac': settings['macs'][1], 'ltt': datetime.datetime(2018, 5, 15, 5, 40, 5), 'ip': '192.168.0.11'}
            ]

        )

    def test_anyonehome(self):
        with open('./settings.json') as f:
            settings = json.load(f)
        leases = porch.read_leases('./dhcpd.leases.bak', settings['macs'])
        dt = datetime.datetime(2018, 5, 15, 5, 43, 00)
        self.assertTrue(porch.anyone_home(dt, leases))
        dt = datetime.datetime(2018, 5, 15, 5, 45, 00)
        self.assertTrue(porch.anyone_home(dt, leases))
        dt = datetime.datetime(2018, 5, 15, 5, 50, 00)
        self.assertFalse(porch.anyone_home(dt, leases))
        dt = datetime.datetime.utcnow()
        self.assertFalse(porch.anyone_home(dt, leases))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(PorchTest)
    suite.run(None)
