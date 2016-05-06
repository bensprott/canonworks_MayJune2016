'''
Created on Feb 4, 2016

@author: BenGaming
'''

from functools import wraps
from flask import abort
from flask_login import current_user
from models import Permission

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission) :
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    '''
        a decorator for an admin required function
    '''
    return permission_required(Permission.ADMINISTER)(f)

def mod_required(f):
    '''
        a decorator to ensure a function is not called
        unless a user has moderator role.
    '''
    return permission_required(Permission.MODERATE_COMMENTS)(f)

def write_required(f):
    '''
        a decorator to ensure that a user has write 
        privileges.
    '''
    return permission_required(Permission.WRITE_ARTICLES)(f)
    