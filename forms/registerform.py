from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, EmailField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange


class RegisterForm(FlaskForm):
    email = EmailField('Login / email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 20)])
    password2 = PasswordField('Repeat password', validators=[DataRequired(), EqualTo('password')])
    surname = StringField('Surname', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(14, 100)])
    pfp = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Submit')
