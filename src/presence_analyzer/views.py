# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import redirect, abort
from flask.ext.mako import render_template
import locale
from mako.exceptions import TopLevelLookupException

from presence_analyzer.main import app
from presence_analyzer.utils import (
    get_data,
    get_users_data,
    group_by_month_and_year,
    group_by_weekday,
    group_start_end_time_by_weekday,
    jsonify,
    mean
)

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name

locale.setlocale(locale.LC_COLLATE, 'pl_PL.UTF-8')


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/presence_weekday')


@app.route('/<string:view_name>')
def views(view_name):
    """
    View for rendering template based on url.
    """
    try:
        return render_template('%s.html' % view_name)
    except TopLevelLookupException:
        abort(404)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Sorted users listing for dropdown.
    """
    data = get_users_data()
    result = [
        {
            'user_id': i,
            'name': data[i].get('name', 'User {0}'.format(i)),
        }
        for i in data.keys()
    ]

    result.sort(key=lambda x: x['name'], cmp=locale.strcoll)
    return result


@app.route('/api/v1/users/<int:user_id>', methods=['GET'])
@jsonify
def users_data_view(user_id):
    """
    Returns user's real name and link to avatar.
    """
    data = get_users_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    return {
        'real_name': data[user_id].get('name', None),
        'avatar': data[user_id].get('avatar', None),
    }


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/start_end_weekday/<int:user_id>', methods=['GET'])
@jsonify
def start_end_weekday(user_id):
    """
    Returns mean start and end time of user by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_start_end_time_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], start, end)
        for weekday, (start, end) in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/month_and_year/<int:user_id>', methods=['GET'])
@jsonify
def month_and_year_presence(user_id):
    """
    Returns total presence time of give user grouped by month and year.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    year_months = group_by_month_and_year(data[user_id])
    result = [
        (year_month, sum(intervals))
        for year_month, intervals in year_months.items()
    ]
    return result
