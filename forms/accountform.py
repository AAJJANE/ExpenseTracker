from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, IntegerField
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import DateField, DateTimeField, DateTimeLocalField
from wtforms.fields.numeric import DecimalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, InputRequired


class AddAccountForm(FlaskForm):
    type = SelectField('Type', validators=[DataRequired()],
                                choices=[('income', 'income'),
                                        ('expense', 'expense')])
    category = StringField("Category", validators=[DataRequired()])
    date = DateField('Date', validators=[InputRequired()])
    amount = DecimalField('Amount', validators = [DataRequired()])
    submit = SubmitField('Generate Report')
