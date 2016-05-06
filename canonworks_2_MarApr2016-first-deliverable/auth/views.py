from flask_login import current_user, login_required, login_user
from flask import current_app, render_template, flash, redirect, request, url_for
from forms import *
from . import auth
from models import alchemyDB
from werkzeug.security import generate_password_hash


@auth.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_name = form.username.data).first()  # @UndefinedVariable
        if user and user.is_banned() :
            flash("This account has been banned!")
            return render_template('auth/login.html', form = form)
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index')) # @UndefinedVariable
        flash('Invalid username or password.')    
    return render_template('auth/login.html', form = form)


@auth.route('/change_password', methods = ['GET', 'POST'])
@login_required
def change_password():
    '''
        This allows a user to change his password.
    '''
    form = ChangePassword()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data) : # @UndefinedVariable
            current_user.user_pass =  generate_password_hash(form.new_password.data)
            alchemyDB.session.commit() # @UndefinedVariable
            flash("Password Updated")   
            return redirect(url_for('user_profile')) 
        else :
            flash("Invalid old password!")
    return render_template('auth/change_password.html', form = form)


