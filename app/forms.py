from wtforms import Form, StringField, PasswordField, validators, BooleanField

class RegistrationForm(Form):
    name = StringField('Username', [validators.Length(min=4, max=256)])
    email = StringField('Email Address', [validators.Length(min=6, max=256)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

class LoginForm(Form):
    name_email = StringField('Username or Email', [validators.Length(min=4, max=256)])
    password = PasswordField('Password', [validators.DataRequired()])
    remember = BooleanField('Remember Me!', [validators.AnyOf([True, False])])