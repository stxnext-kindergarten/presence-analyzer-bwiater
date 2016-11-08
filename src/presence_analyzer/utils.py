# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
from json import dumps
from functools import wraps
from datetime import datetime, timedelta
from threading import Lock
from copy import deepcopy
import hashlib
import pickle

from flask import Response
from lxml import etree

from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


cached = {}


def compute_key(function, args, kwargs):
    key = pickle.dumps((function.func_name, args, kwargs))
    return hashlib.sha1(key).hexdigest()


def cache(seconds):
    """
    Cache result of function for the time specified by 'seconds' parametr.
    """
    def wrapper(function):
        @wraps(function)
        def inner(*args, **kwargs):
            """
            This docstring will be overridden by @wraps decorator.
            """
            with Lock():
                key = compute_key(function, args, kwargs)
                if key in cached:
                    cache_is_obsolete = (
                        datetime.now() - cached[key]['datetime'] >
                        timedelta(seconds=seconds)
                    )
                    if not cache_is_obsolete:
                        return cached[key]['data']
                cached[key] = {
                    'datetime': datetime.now(),
                    'data': function(),
                }
                return cached[key]['data']
        return inner
    return wrapper


@cache(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def get_users_data():
    """
    It upgrades get_data() result with user's name and avatar from XML
    file.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
            'avatar': 'intranet.stxnext.pl/api/images/users/10',
            'name': 'Jan K.'
        }
    }
    """
    data = deepcopy(get_data())
    name_reader = etree.parse(app.config['DATA_XML'])
    server = name_reader.find('server')
    avatar_base_url = '{0}://{1}'.format(
        server.find('protocol').text,
        server.find('host').text
    )
    for user in name_reader.find('users').findall('user'):
        user_id = int(user.attrib['id'])
        data.setdefault(user_id, {})['avatar'] =\
            '{0}{1}'.format(
                avatar_base_url,
                user.find('avatar').text
        )
        data[user_id]['name'] = user.find('name').text

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def group_start_end_time_by_weekday(items):
    """
    Groups mean start and end time by weekday.
    """
    time = [{'start': [], 'end': []} for i in range(7)]
    for date in items:
        time[date.weekday()]['start'].append(
            seconds_since_midnight(items[date]['start']))
        time[date.weekday()]['end'].append(
            seconds_since_midnight(items[date]['end']))

    result = [[] for i in range(7)]
    for weekday, values in enumerate(time):
        result[weekday] = [mean(values['start']), mean(values['end'])]

    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0
