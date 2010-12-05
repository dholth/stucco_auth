import datetime
from pyramid.view import view_config
from pyramid import security
from pyramid.url import model_url
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from ponzi_auth import tables
from sqlalchemy.orm.exc import NoResultFound

import logging
log = logging.getLogger(__name__)

def get_dbsession(request):
    # XXX this is lame
    try:
        return request.db
    except:
        request.db = request.registry.settings['ponzi_auth.db_session_factory']()
        return request.db

@view_config(name='login',
             renderer='login.html')
def login(request, username=None):
    logged_in = bool(username or security.authenticated_userid(request))

    if logged_in:
        return {'logged_in': True,
                'form_enabled': False,
                'status': u'Already logged in',
                'status_type': u'info'}

    status = u''
    status_type = u''
    if request.method == 'POST' and 'form.submitted' in request.params:
        status_type = u'error'
        status = u'Invalid username and/or password'
        dbsession = get_dbsession(request)
        try:
            username = request.params['username']
            user = dbsession.query(tables.User).filter_by(username=username).one()
            if user.check_password(request.params['password']):
                came_from = request.params.get('came_from',
                                               model_url(request.root, request))
                return HTTPFound(location=came_from,
                                 headers=security.remember(request, username))
        except NoResultFound:
            # just use above error msg
            pass

    return {
        'form_enabled': True,
        'status_type': status_type,
        'status': status,
        'logged_in': False,
        'username': request.params.get('username', u''),
        'allow_signup': request.registry.settings.get('ponzi_auth.allow_signup') or False,
        'allow_password_reset': request.registry.settings.get('ponzi_auth.allow_password_reset') or False,
        }


@view_config(name='sign-up',
             renderer='sign-up.html')
def signup(request):
    if not request.registry.settings.get('ponzi_auth.allow_signup'):
        raise NotFound()

    status = u''
    status_type = u''
    if request.method == 'POST' and 'form.submitted' in request.params:
        dbsession = get_dbsession(request)
        user_count = dbsession.query(tables.User).filter_by(username=request.params['username']).count()
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
            dbsession.add(user)
            dbsession.commit()
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

@view_config(name='logout')
def logout(request):
    came_from = request.params.get('came_from',
                                   model_url(request.root, request))
    return HTTPFound(location=came_from,
                     headers=security.forget(request))

def find_user(request, username=None):
    username = username or security.authenticated_userid(request)
    if not username:
        return None
    db_session = get_dbsession(request)
    return db_session.query(tables.User).filter_by(username=username).one()

def find_groups(user, request):
    if isinstance(user, basestring):
        user = find_user(request, user)
    if user is None:
        return []

    return user.groups
