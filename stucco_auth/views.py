from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid
from pyramid.security import remember, forget
from pyramid.url import resource_url

from stucco_auth.security import authenticate

import logging
log = logging.getLogger(__name__)


def login(request):
    """Login view for GET requests."""
    logged_in = authenticated_userid(request) is not None

    if logged_in:
        return {'logged_in': True,
                'form_enabled': False,
                'status': u'Already logged in',
                'status_type': u'info'}

    status = u''
    status_type = u''

    return {
        'form_enabled': True,
        'status_type': status_type,
        'status': status,
        'logged_in': False,
        'username': request.params.get('username', u''),
        }


def login_post(request):
    """Login view for POST requests."""
    context = request.context
    login_url = resource_url(context, request, 'login')
    next_url = request.params.get('next', request.referrer)
    if not next_url or next_url == login_url:
        # never use the login form itself as next_url
        next_url = request.application_url + '/'

    message = ''
    headers = []

    if 'form.submitted' in request.POST:
        login = request.POST['username']
        password = request.POST['password']
        user = authenticate(request.db, login, password)
        if not user:
            message = u'Failed login.'
        elif user.is_active:
            request.session.invalidate()
            headers = remember(request, user.user_id)
        else:
            message = u'Failed login. That account is not active.'

    if message:
        request.session.flash(message)

    return HTTPFound(location=next_url, headers=headers)


def logout(request):
    request.session.delete()
    next_url = request.params.get('next', resource_url(request.root, request))
    return HTTPFound(location=next_url, headers=forget(request))


def view_model(request):
    """Do-nothing view. Template will reference request.context"""
    return {}
