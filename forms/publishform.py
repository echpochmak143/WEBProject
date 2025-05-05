from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired


class PublishForm(FlaskForm):
    title = StringField(validators=[DataRequired()])
    content = StringField(validators=[DataRequired()])
    con = TextAreaField(validators=[DataRequired()])
    file = FileField(validators=[DataRequired()])
    photo = FileField(validators=[DataRequired()])
    submit = SubmitField(validators=[DataRequired()])
