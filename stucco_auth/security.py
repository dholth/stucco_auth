from stucco_auth.tables import User
from stucco_auth.views import get_dbsession
import pyramid.security

def lookup_groups(authenticated_userid, request):
    """Return a list of group identifiers for the authenticated user,
    or [] if the user was not found.
    
    Called by the authentication policy. View code can use
    pyramid.security.effective_principals(request)"""
    user = request.db.query(User).get(authenticated_userid)
    if user is None:
        return []
    return [str(g) for g in user.groups]

find_groups = lookup_groups # bw compat
