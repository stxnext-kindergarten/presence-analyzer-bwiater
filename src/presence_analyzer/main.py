# -*- coding: utf-8 -*-
"""
Flask app initialization.
"""
from flask import Flask
from flask.ext.mako import MakoTemplates
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_user import SQLAlchemyAdapter, UserManager

app = Flask(__name__)  # pylint: disable=invalid-name
MakoTemplates(app)

db = SQLAlchemy(app)


def register_login_manager(app):
    """
    Creates app.login_manager.
    """
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'


def register_user_manager():
    """
    Creates app.user_manager and database.
    Call it after loading config which contains 'SECRET_KEY'.
    """
    from models import User
    from forms import LoginForm, RegisterForm
    db_adapter = SQLAlchemyAdapter(db, User)

    try:
        app.user_manager
    except AttributeError:
        UserManager(
            db_adapter,
            app=app,
            login_form=LoginForm,
            register_form=RegisterForm
        )

    db.create_all()
    return db_adapter


register_login_manager(app)
