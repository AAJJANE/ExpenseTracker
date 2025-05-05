from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.fields.datetime import DateField
from wtforms.validators import InputRequired


class PeriodForm(FlaskForm):
    start_date = DateField('Start date', validators=[InputRequired()])
    end_date = DateField('End date', validators=[InputRequired()])
    submit = SubmitField('Done')
