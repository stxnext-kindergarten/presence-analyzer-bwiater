# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from datetime import datetime
from flask import redirect, request, abort
from flask.ext.mako import render_template
from flask_login import login_user, logout_user
from flask_user import login_required
import locale
from mako.exceptions import TopLevelLookupException

from presence_analyzer.main import app
from presence_analyzer.utils import (
    get_data,
    get_months,
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


@app.route('/user/register/', methods=['GET', 'POST'])
def register():
    """
    Register view. On GET returns form with username and password fields.
    On POST validates form, if valid redirects to login view.
    """
    user_manager = app.user_manager
    db_adapter = user_manager.db_adapter
    register_form = user_manager.register_form(request.form)

    if request.method == 'POST' and register_form.validate():
        user_fields = {
            'username': register_form.data['username'],
            'password': user_manager.hash_password(
                register_form.data['password']
            ),
        }
        db_adapter.add_object(db_adapter.UserClass, **user_fields)
        db_adapter.commit()
        return redirect('/user/login/')

    return render_template('register.html', form=register_form)


@app.route('/user/login/', methods=['GET', 'POST'])
def login():
    """
    Login view. On GET returns form with username and password fields.
    On POST validates form, if valid then login user and redirects to
    next or '/'.
    """
    user_manager = app.user_manager
    login_form = user_manager.login_form(request.form)

    if request.method == 'POST' and login_form.validate_on_submit():
        user = user_manager.find_user_by_username(login_form.username.data)
        if user:
            login_user(user)
            return redirect(request.args.get('next') or '/')

    return render_template('login.html', form=login_form)


@app.route('/user/logout/', methods=['GET'])
@login_required
def logout():
    """
    Logout current user. If success redirects to /logout-success/ and
    renders logout_success.html template.
    """
    logout_user()
    return render_template('logout_success.html')


@app.route('/<string:view_name>')
@login_required
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


@app.route('/api/v1/months', methods=['GET'])
@jsonify
def months_view():
    """
    Sorted year and month listing for dropdown.

    It creates structure like this:
    data = [
        {'year': 2011, 'month': 1, 'text': '2011-January'},
        {'year': 2011, 'month': 2, 'text': '2011-February'},
        {'year': 2013, 'month': 9, 'text': '2013-September'},
    ]
    """
    data = get_months()
    result = [
        {
            'year': datetime.strptime(date, '%Y-%B').year,
            'month': datetime.strptime(date, '%Y-%B').month,
            'text': date,
        }
        for date in data
    ]

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


@app.route('/api/v1/top_employees/<int:year>/<int:month>', methods=['GET'])
@jsonify
def employees_in_year_month(year, month):
    """
    Returns top 5 employees in month and year.

    It returns structure like this:
    data = [
        {
            'presence_time': 118402,
            'id': 11,
            'name': 'User 11',
            'avatar': None
        },
        {
            'presence_time': 78217,
            'id': 10,
            'name': 'Jan P.',
            'avatar': 'https://intranet.stxnext.pl/api/images/users/10'
        },
        {
            'presence_time': 0,
            'id': 12,
            'name': 'Patryk G.',
            'avatar': 'https://intranet.stxnext.pl/api/images/users/12'
        },
    ]
    """
    data = get_data()
    result = []
    year_month = '{0}-{1:02}'.format(year, month)
    for user_id in data:
        grouped = group_by_month_and_year(data[user_id])
        result.append({
            'id': user_id,
            'presence_time': sum(grouped[year_month]),
        })

    result.sort(key=lambda x: x['presence_time'], reverse=True)
    result = result[:5]

    users_data = get_users_data()
    for user in result:
        user_id = user['id']
        user.update(
            name=users_data[user_id].get('name', 'User {0}'.format(user_id)),
            avatar=users_data[user_id].get('avatar', None),
        )

    return result
