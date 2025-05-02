from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.choices import SelectField
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import DecimalField
from wtforms.validators import DataRequired, NumberRange, InputRequired


class AddAccountForm(FlaskForm):
    type = SelectField('Type', validators=[DataRequired()],
                       choices=[('income', 'income'),
                                ('expense', 'expense')])
    category = StringField("Category", validators=[DataRequired()])
    date = DateField('Date', validators=[InputRequired()])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Done')
