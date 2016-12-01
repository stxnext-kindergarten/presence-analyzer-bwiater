# -*- coding: utf-8 -*-
"""
Defines forms.
"""
from flask_wtf.form import FlaskForm
from wtforms import HiddenField, PasswordField, TextField, validators
from presence_analyzer.main import app


class LoginOrRegisterForm(FlaskForm):
    """
    Base form for LoginForm and RegisterForm. Defines username and
    password fields. Both fields are required.
    """

    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])


class LoginForm(LoginOrRegisterForm):
    """
    Login form.
    """

    def validate(self):
        """
        Call super(LoginForm, self).validate() then checks if user
        exists, if so, verifies password. If user exists and password is
        valid returns True.
        """
        if not super(LoginForm, self).validate():
            return False

        user = None
        user_manager = app.user_manager

        if user_manager.enable_username:
            user = user_manager.find_user_by_username(self.username.data)
            is_valid = (
                user and
                user.password and
                user_manager.verify_password(self.password.data, user)
            )

            if is_valid:
                return True

            if user_manager.show_username_email_does_not_exist:
                if not user:
                    self.username.errors.append('User does not exist.')
                else:
                    self.password.errors.append('Incorrect password.')

        return False


class RegisterForm(LoginOrRegisterForm):
    """
    Register form.
    """

    def validate_username(self, field):
        """
        Checks if username has been choosen before, if so, raises
        ValidationError.
        """
        db_adapt = app.user_manager.db_adapter
        if db_adapt.find_first_object(db_adapt.UserClass, username=field.data):
            raise validators.ValidationError('Username is already used.')
