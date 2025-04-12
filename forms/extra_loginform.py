from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired


from .loginform import LoginForm

class ExtraLoginForm(FlaskForm):
    username = IntegerField('Id астронавта', validators=[DataRequired()])
    password = PasswordField('Пароль астронавта', validators=[DataRequired()])
    submit = SubmitField('Войти')

