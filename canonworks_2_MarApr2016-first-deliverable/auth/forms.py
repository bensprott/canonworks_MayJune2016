'''
Created on Nov 26, 2014

@author: Ben
'''
from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import Required, Email, Length, Regexp, EqualTo
from wtforms import ValidationError, validators
from models import User
from flask_pagedown.fields import PageDownField
from wtforms.fields.simple import HiddenField


class PrivateMessageReply(Form):
    '''
        A form for a reply to a private message
    '''
    title = TextAreaField("Title", validators=[Required()])
    text = PageDownField("Text", validators=[Required()])
    original_messageID = HiddenField()
    srcLibEntries = HiddenField(label=None, id="srcLibArticles")
    submit = SubmitField('Send Message', id="new_entry_submit_button")


class NewPrivateMessage(Form):
    '''
        a form for a new private message
    '''
    title = TextAreaField("Title", validators=[Required()])
    text = PageDownField("Text", validators=[Required()])
    srcLibEntries = HiddenField(label=None, id="srcLibArticles")
    submit = SubmitField('Send Message', id="new_entry_submit_button")



class NewEntry(Form):
    '''
        A form for new entries
    '''
    title = TextAreaField("Title", validators=[Required()])
    text = PageDownField("Text", validators=[Required()])
    tags = TextAreaField("Tags", validators=[Required(validators.Required('Please add some tags.'))])
    srcLibEntries = HiddenField(label=None, id="srcLibArticles")
    submit = SubmitField('Submit', id="new_entry_submit_button")


class LoginForm(Form):
    username = StringField('User Name', validators = [Required(), Length(min = 1, max = 15)])    
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')
    
class RegistrationForm(Form):
    email =  StringField('Email', validators = [Required(), Length(1,64), Email()])
    username = StringField('Username', validators = [Required(), Length(1,64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password', validators=[Required(), EqualTo('password2', message = 'Passwords must match.')])
    password2 = PasswordField('Confirm password', validators = [Required()])
    submit = SubmitField('Register')
    
    def validate_email(self, field):
        if User.query.filter_by(user_email = field.data).first():  # @UndefinedVariable
            raise ValidationError('Email already registered.')
        
    def validate_username(self, field):
        if User.query.filter_by(user_name = field.data).first() :  # @UndefinedVariable
            raise ValidationError('Username already in use.')

class ChangePassword(Form):
    '''
        a form to allow users to change their password.
    '''
    old_password = PasswordField('Old Password', validators=[Required()])
    new_password = PasswordField('New Password', validators=[Required(), EqualTo('new_password2', message = 'Passwords must match.')])
    new_password2 = PasswordField('Confirm New Password', validators = [Required()])
    submit = SubmitField('Change Password')
    
class ForgotPassword(Form):
    '''
        If a user forgets their password, then they use this
        form to enter their email and receive a password reset.
    '''
    email =  StringField('Email', validators = [Required(), Length(1,64), Email()])
    submit = SubmitField('Reset Password')    
    
    
    
class ResetPassword(Form):
    '''
        If a user forgets their password, they can have a link
        sent to their email account which allows them to reset their password.
        This form allows for that password reset.        
    '''
    new_password = PasswordField('New Password', validators=[Required(), EqualTo('new_password2', message = 'Passwords must match.')])
    new_password2 = PasswordField('Confirm New Password', validators = [Required()])
    submit = SubmitField('Reset Password')
    

class ChangeEmail(Form):
    '''
        a form that allows users to change their email address.
    '''    
    email =  StringField('Email', validators = [Required(), Length(1,64), Email()])
    submit = SubmitField('Change Email Address')