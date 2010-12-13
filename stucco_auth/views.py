from jinja2 import Markup, escape
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.security import view_execution_permitted
from pyramid.security import authenticated_userid
from pyramid.security import remember, forget
from pyramid.url import model_url
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound

from stucco_auth import tables
from stucco_auth.util import get_flash, set_flash
from stucco_auth.interfaces import IAuthRoot
from stucco_auth.security import authenticate

import datetime

import logging
log = logging.getLogger(__name__)

def get_dbsession(request):
    """Return SQLAlchemy session for request."""
    return request.db

@view_config(name='login',
             renderer='login.html',
             context=IAuthRoot,
             permission='view')
def login(request):
    logged_in = authenticated_userid(request) is not None

    if logged_in:
        return {'logged_in': True,
                'form_enabled': False,
                'status': u'Already logged in',
                'status_type': u'info'}

    status = u''
    status_type = u''    
    signup_link = u''
    password_reset_link = u''
    if view_execution_permitted(request.context, request, name='signup'):
        # true even if the view does not exist. Lookup IView for context,
        # request?, name as well...
        signup_link = Markup(
        """<div class="login-action signup"><a href="%s">Sign up for a new account.</a></div>""" % 
        escape(request.relative_url('signup'))
        )

    if view_execution_permitted(request.context, request, name='passswordreset'):
        # I often wonder if this isn't the primary login mechanism:
        password_reset_link = Markup(
        """<div class="login-action passwordreset"><a href="%s">Forgot password?</a></div>""" %
        escape(request.relative_url('passwordreset'))
        )

    return {
        'form_enabled': True,
        'status_type': status_type,
        'status': status,
        'logged_in': False,
        'username': request.params.get('username', u''),
        'signup_link':signup_link,
        'password_reset_link':password_reset_link,
        }
    
@view_config(name='login',
             context=IAuthRoot,
             permission='view',
             request_method='POST')
def login_post(request):
    context = request.context    
    login_url = model_url(context, request, 'login')
    came_from = request.params.get('came_from', request.referrer)
    if not came_from or came_from == login_url:
        # never use the login form itself as came_from
        came_from = request.application_url + '/'
        
    if request.method != 'POST':
        return HTTPFound(location=came_from)

    message = ''
    login = ''
    password = ''
    headers = []

    if 'form.submitted' in request.params:
        login = request.POST['username']
        password = request.POST['password']
        user = authenticate(request.db, login, password)
        if user and user.is_active:
            request.session.invalidate()
            headers = remember(request, user.user_id)                            
        elif user and not user.is_active:
            message = u'Failed login. That account is not active.'
        else:
            message = u'Failed login. ' + \
                Markup(u"<a href='%s'>Forgot password?</a>" 
                       % escape(model_url(context, request, 'passwordreset')))

    if message:
        set_flash(request, message)

    return HTTPFound(location=came_from, headers=headers)       

@view_config(name='logout',
             context=IAuthRoot)
def logout(request):
    request.session.delete()
    came_from = request.params.get('came_from',
                                   model_url(request.root, request))
    return HTTPFound(location=came_from,
                     headers=forget(request))

@view_config(name='sign-up',
             renderer='sign-up.html',
             context=IAuthRoot,
             permission='sign-up')
def signup(request):
    if not request.registry.settings.get('stucco_auth.allow_signup'):
        raise NotFound()

    status = u''
    status_type = u''
    if request.method == 'POST' and 'form.submitted' in request.params:
        user_count = request.db.query(tables.User)\
            .filter_by(username=request.params['username']).count()
        status_type = u'error'
        if user_count > 0:
            status = u'Username already taken'
        else:
            status = u'Error creating account'
            now = datetime.datetime.now()
            user = tables.User(username=request.params['username'],
                               is_active=True,
                               date_joined=now,
                               last_password_change=now)
            for f in ('firstname', 'lastname'):
                if f in request.params:
                    setattr(user, f, request.params[f])
            user.set_password(request.params['password'])
            request.db.add(user)
            status = u'Account created'
            status_type = u'info'

    return {
        'status_type': status_type,
        'status': status,
        'username': request.params.get('username', u'')
        }

def view_plural(request):
    """Generic view for a simple collection."""
    return {'items':list(request.context)}

def view_model(request):
    """Do-nothing view. Template will reference request.context"""
    return {}

