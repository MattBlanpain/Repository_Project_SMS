from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import User

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name',
                           validators=[DataRequired(), Length(min=2, max=20)])
    last_name = StringField('Last Name',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_first_name(self, first_name):
        user = User.query.filter_by(first_name=first_name.data).first()
        if user:
            raise ValidationError('That first name is taken. Please choose a different one.')

    def validate_last_name(self, last_name):
        user = User.query.filter_by(last_name=last_name.data).first()
        if user:
            raise ValidationError('That last name is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    first_name = StringField('First Name',
                           validators=[DataRequired(), Length(min=2, max=20)])
    last_name = StringField('Last Name',
                           validators=[DataRequired(), Length(min=2, max=20)])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_first_name(self, first_name):
        if first_name.data != current_user.first_name:
            user = User.query.filter_by(first_name=first_name.data).first()
            if user:
                raise ValidationError('That first name is taken. Please choose a different one.')

    def validate_last_name(self, last_name):
        if last_name.data != current_user.last_name:
            user = User.query.filter_by(last_name=last_name.data).first()
            if user:
                raise ValidationError('That last name is taken. Please choose a different one.')

