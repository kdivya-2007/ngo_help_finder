from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField
from wtforms.validators import DataRequired,Length,Email,EqualTo

class RegistrationForm(FlaskForm):
    username=StringField('username',validators=[DataRequired(),Length(min=2,max=20)])
    email=StringField('email',validators=[DataRequired(),Email()])
    password=PasswordField('password',validators=[DataRequired()])
    confirm_password=PasswordField('confirm password',validators=[DataRequired(),EqualTo('password')])
    submit=SubmitField('sign up')
class LoginForm(FlaskForm):
    
    email=StringField('email',validators=[DataRequired(),Email()])
    password=PasswordField('password',validators=[DataRequired()])
    remember=BooleanField('Remember Me')
    submit=SubmitField('Login')
class RequestResetForm(FlaskForm):
    email = StringField('Email',
        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password',
        validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
        validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
class AddNGOForm(FlaskForm):
    name = StringField('NGO Name', validators=[DataRequired()])
    district = StringField('District', validators=[DataRequired()])
    address = StringField('Address')
    contact = StringField('Contact')
    needs = StringField('Needs')
    latitude = StringField('Latitude')
    longitude = StringField('Longitude')
    submit = SubmitField('Add NGO')       