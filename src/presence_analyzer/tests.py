# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)

TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({
            'DATA_CSV': TEST_DATA_CSV,
            'DATA_XML': TEST_DATA_XML,
        })
        self.client = main.app.test_client()
        utils.cached = {}

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        utils.cached = {}

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_views(self):
        """
        Test views.
        """
        views_name = [
            'presence_weekday',
            'mean_time_weekday',
            'presence_start_end',
            'month_and_year',
        ]
        for name in views_name:
            self.assertEqual(self.client.get('/%s' % name).status_code, 200)

    def test_views_404(self):
        """
        Test views returns 404 if template for view does not exist.
        """
        self.assertEqual(self.client.get('/fake_url').status_code, 404)

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        sample_date = [
            {'user_id': 10, 'name': 'Jan P.'},
            {'user_id': 11, 'name': 'User 11'},
            {'user_id': 12, 'name': 'Patryk G.'},
        ]
        self.assertEqual(json.loads(resp.data), sample_date)

    def test_users_data_api_view(self):
        """
        Test user data view.
        """
        resp = self.client.get('/api/v1/users/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        sample_date = {
            'avatar': 'https://intranet.stxnext.pl/api/images/users/10',
            'real_name': 'Jan P.',
        }
        self.assertDictEqual(json.loads(resp.data), sample_date)

    def test_users_data_api_view_404(self):
        """
        Test users data view returns 404 if user does not exist.
        """
        self.assertEqual(self.client.get('/api/v1/users/0').status_code, 404)

    def test_api_mean_time_weekday(self):
        """
        Test mean time weekday's result.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(json.loads(resp.data), [
            ['Mon', 0],
            ['Tue', 30047.0],
            ['Wed', 24465.0],
            ['Thu', 23705.0],
            ['Fri', 0],
            ['Sat', 0],
            ['Sun', 0]
        ])

    def test_api_mean_time_weekday_404(self):
        """
        Test mean time weekday returns 404 if user does not exist.
        """
        self.assertEqual(
            self.client.get('/api/v1/mean_time_weekday/0').status_code,
            404
        )

    def test_presence_weekday(self):
        """
        Test presence weekday's result.
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(json.loads(resp.data), [
            ['Weekday', 'Presence (s)'],
            ['Mon', 0],
            ['Tue', 30047.0],
            ['Wed', 24465.0],
            ['Thu', 23705.0],
            ['Fri', 0],
            ['Sat', 0],
            ['Sun', 0]
        ])

    def test_presence_weekday_404(self):
        """
        Test presence weekday returns 404 if user does not exist.
        """
        self.assertEqual(
            self.client.get('/api/v1/presence_weekday/0').status_code,
            404
        )

    def test_start_end(self):
        """
        Test start end weekday's result.
        """
        resp = self.client.get('/api/v1/start_end_weekday/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(json.loads(resp.data), [
            ['Mon', 33134.0, 57257.0],
            ['Tue', 33590.0, 50154.0],
            ['Wed', 33206.0, 58527.0],
            ['Thu', 35602.0, 58586.0],
            ['Fri', 47816.0, 54242.0],
            ['Sat', 0, 0],
            ['Sun', 0, 0]
        ])

    def test_start_end_weekday_404(self):
        """
        Test start end weekday returns 404 if user does not exist.
        """
        self.assertEqual(
            self.client.get('/api/v1/start_end_weekday/0').status_code,
            404
        )

    def test_month_and_year(self):
        """
        Test month and year's results.
        """
        resp = self.client.get('/api/v1/month_and_year/12')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertItemsEqual(json.loads(resp.data), [
            ['2011-01', 19800],
            ['2011-02', 3600],
        ])

    def test_month_and_year_404(self):
        """
        Test month and year returns 404 if user doess not exits.
        """
        self.assertEqual(
            self.client.get('/api/v1/month_and_year/0').status_code,
            404
        )


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({
            'DATA_CSV': TEST_DATA_CSV,
            'DATA_XML': TEST_DATA_XML,
        })
        utils.cached = {}

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        utils.cached = {}

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11, 12])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_group_by_weekday(self):
        """
        Test grouping working time by weekdays.
        """
        data = {
            datetime.date(2016, 10, 17): {
                'start': datetime.time(8, 0, 0),
                'end': datetime.time(16, 0, 0),
            },
            datetime.date(2016, 10, 20): {
                'start': datetime.time(9, 30, 0),
                'end': datetime.time(17, 45, 0),
            },
            datetime.date(2016, 10, 21): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(9, 0, 0),
            },
            datetime.date(2016, 10, 24): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(9, 30, 0),
            },
        }
        self.assertEqual(
            utils.group_by_weekday(data),
            [[28800, 3600], [], [], [29700], [1800], [], []]
        )

    def test_group_start_end_by_weekday(self):
        """
        Test grouping start and end time by weekday.
        """
        data = {
            datetime.date(2016, 10, 17): {
                'start': datetime.time(8, 0, 0),
                'end': datetime.time(16, 0, 0),
            },
            datetime.date(2016, 10, 20): {
                'start': datetime.time(9, 30, 0),
                'end': datetime.time(17, 45, 0),
            },
            datetime.date(2016, 10, 24): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(9, 30, 0),
            },
        }
        self.assertEqual(
            utils.group_start_end_time_by_weekday(data),
            [
                [29700.0, 45900.0],
                [0, 0],
                [0, 0],
                [34200.0, 63900.0],
                [0, 0],
                [0, 0],
                [0, 0]
            ]
        )

    def test_group_by_month_and_year(self):
        """
        Test grouping presence time by month and year.
        """
        data = {
            datetime.date(2016, 10, 17): {
                'start': datetime.time(8, 0, 0),
                'end': datetime.time(16, 0, 0),
            },
            datetime.date(2016, 10, 20): {
                'start': datetime.time(9, 30, 0),
                'end': datetime.time(13, 30, 0),
            },
            datetime.date(2016, 11, 24): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(9, 30, 0),
            },
        }
        self.assertItemsEqual(
            utils.group_by_month_and_year(data),
            {
                '2016-10': [14400, 28800],
                '2016-11': [3600],
            }
        )

    def test_seconds_since_midnight(self):
        """
        Test calculating seconds since midnight.
        """
        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(12, 15, 15)),
            44115
        )

    def test_interval(self):
        """
        Test calculating interval in seconds between two datetime.time objects.
        """
        self.assertEqual(
            utils.interval(
                datetime.time(17, 59, 29),
                datetime.time(18, 2, 15)
            ),
            166
        )

    def test_mean(self):
        """
        Test calculating arithmetic mean.
        """
        self.assertEqual(utils.mean([0, 1, 1, 2, 2]), 1.2)

    def test_mean_empty(self):
        """
        Test mean function returns 0 if list is empty.
        """
        self.assertEqual(utils.mean([]), 0)


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
