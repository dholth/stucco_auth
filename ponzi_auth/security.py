from ponzi_auth.tables import User
from ponzi_auth.views import get_dbsession


class GroupLookupError(Exception):
    pass

def find_user(request, username=None):
    username = username or security.authenticated_userid(request)
    if not username:
        return None
    db_session = get_dbsession(request)
    return db_session.query(User).filter_by(username=username).one()

def find_groups(user, request):
    if isinstance(user, basestring):
        user = find_user(request, user)
    if user is None:
        raise GroupLookupError('Groups lookup not possible, user "%s" does not exist' % userid)

    return [str(u) for u in user.groups]
