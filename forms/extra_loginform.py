from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class ExtraLoginForm(FlaskForm):
    username = IntegerField("User's ID", validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('Log in')
