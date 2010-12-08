from ponzi_auth.tables import User
from ponzi_auth.views import get_dbsession
import pyramid.security


class GroupLookupError(Exception):
    pass

def find_user(request, userinfo=None):
    if userinfo is not None and isinstance(userinfo, int):
        return db_session.query(User).get(userinfo)

    userinfo = userinfo or pyramid.security.authenticated_userid(request)
    if not userinfo:
        return None
    db_session = get_dbsession(request)
    return db_session.query(User).filter_by(username=userinfo).one()

def find_groups(user, request):
    if not isinstance(user, User):
        if isinstance(user, (basestring, int)):
            user = find_user(request, user)
        if user is None:
            raise GroupLookupError('Groups lookup not possible, user "%s" does not exist' % str(user))

    return [str(g) for g in user.groups]
