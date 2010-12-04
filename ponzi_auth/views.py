import datetime
from pyramid.view import view_config
from pyramid.exceptions import NotFound
from ponzi_auth import tables
from sqlalchemy.orm.exc import NoResultFound


def get_dbsession(request):
    return request.registry.settings['ponzi_auth.db_session_factory']()

@view_config(name='login',
             renderer='login.html')
def login(request):
    status = u''
    status_type = u''
    if request.method == 'POST' and 'form.submitted' in request.params:
        status_type = u'error'
        status = u'Invalid username and/or password'
        dbsession = get_dbsession(request)
        try:
            user = dbsession.query(tables.User).filter_by(username=request.params['username']).one()
            if user.check_password(request.params['password']):
                status = u'Successfully logged in'
                status_type = u'info'
        except NoResultFound:
            # just use above error msg
            pass

    return {
        'status_type': status_type,
        'status': status,
        'username': request.params.get('username', u''),
        'allow_signup': request.registry.settings.get('ponzi_auth.allow_signup'),
        'allow_password_reset': request.registry.settings.get('ponzi_auth.allow_password_reset'),
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
