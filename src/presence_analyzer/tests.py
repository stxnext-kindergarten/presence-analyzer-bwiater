# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals
import os
import json
import datetime
import unittest

from presence_analyzer import forms, main, views, utils, models


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)

TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
)

TEST_DATABASE = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_db.sqlite'
)

TEST_USER_USERNAME = 'testuser'
TEST_USER_PASSWORD = 'passWORD1234'


class PresenceAnalyzerTestCase(unittest.TestCase):
    """
    Base class for tesing user and login functions.
    """
    @classmethod
    def setUpClass(cls):
        """
        Before the first test, sets up configuration for UserManager,
        creates test database. Inserts test user into db.
        """
        main.app.config.update({
            'SECRET_KEY': 'KEY',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + TEST_DATABASE,
            'USER_LOGIN_URL': '/user/login/',
            'USER_REGISTER_URL': '/user/register/',
            'WTF_CSRF_ENABLED': False,
            'USER_PASSWORD_HASH': 'plaintext',
            'HASH_ROUNDS': 1
        })
        db_adapter = main.register_user_manager()
        db_adapter.add_object(
            models.User,
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD,
        )
        db_adapter.commit()

    @classmethod
    def tearDownClass(cls):
        """
        Removes test database.
        """
        os.remove(TEST_DATABASE)


def make_app_context(func):
    def func_wrapper(*args, **kwargs):
            with main.app.app_context():
                return func
    return func_wrapper


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(PresenceAnalyzerTestCase):
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

    def login(self, username, password):
        """
        Login user.
        """
        return self.client.post(
            '/user/login/',
            data=dict(
                username=username,
                password=password
            ),
            follow_redirects=True
        )
    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_register_view_creates_user_and_redirects(self):
        """
        Test register view creates user when valid form is submitted and
        after that redirects to login view.
        """
        self.assertIsNone(
            main.app.user_manager.find_user_by_username('bill')
        )
        resp = self.client.post(
            '/user/register/',
            data=dict(
                username='bill',
                password='bill_password'
            )
        )
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/user/login/')
        self.assertIsNotNone(
            main.app.user_manager.find_user_by_username('bill')
        )

    def test_views(self):
        """
        Test views for logged user.
        """
        views_name = [
            'presence_weekday',
            'mean_time_weekday',
            'presence_start_end',
            'month_and_year',
            'user/logout/',
        ]
        with self.client:
            self.login(TEST_USER_USERNAME, TEST_USER_PASSWORD)
            for name in views_name:
                self.assertEqual(
                    self.client.get('/%s' % name).status_code,
                    200
                )

    def test_views_404(self):
        """
        Test views returns 404 for logged user if template for view does
        not exist.
        """
        with self.client:
            self.login(TEST_USER_USERNAME, TEST_USER_PASSWORD)
            self.assertEqual(self.client.get('/fake_url').status_code, 404)

    def test_api_users(self):
        """
        Test sorted users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        sample_date = [
            {'user_id': 11, 'name': 'Jan K.'},
            {'user_id': 10, 'name': 'Jan P.'},
            {'user_id': 13, 'name': 'Łukasz K.'},
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


class PresenceAnalyzerFormsTestCase(PresenceAnalyzerTestCase):
    """
    Register and login forms tests.
    """

    @make_app_context
    def test_login_register_form_requires_fields_values(self):
        """
        Test LoginOrRegisterForm shows errors on lack of fields values.
        """
        form = forms.LoginOrRegisterForm()
        self.assertFalse(form.validate())
        self.assertIn('This field is required.', form.username.errors)
        self.assertIn('This field is required.', form.password.errors)

    @make_app_context
    def test_login_register_form_is_valid(self):
        """
        Test LoginOrRegisterForm provided with username and password
        is valid.
        """
        form = forms.LoginOrRegisterForm(
            username='username',
            password='password',
        )
        self.assertTrue(form.validate())

    @make_app_context
    def test_login_form_user_does_not_exist_error(self):
        """
        Test LoginForm validate if user does not exist.
        """
        form = forms.LoginForm(
            username='username',
            password='password',
        )
        self.assertFalse(form.validate())
        self.assertIn('User does not exist.', form.username.errors)

    @make_app_context
    def test_login_form_user_validates_password(self):
        """
        Test LoginForm shows error message if password is not valid.
        """
        form = forms.LoginForm(
            username='testuser',
            password='password',
        )
        self.assertFalse(form.validate())
        self.assertIn('Incorrect password.', form.password.errors)

    @make_app_context
    def test_register_form_validates_username_collide(self):
        """
        Test RegisterForm find username collide.
        """
        register_form = forms.RegisterForm(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD,
        )
        self.assertFalse(register_form.validate())
        self.assertIn(
            'Username is already used.',
            register_form.username.errors
        )


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerFormsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
