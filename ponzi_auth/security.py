from ponzi_auth.tables import User

def lookup_groups(userid, request):
    """Return a list of group identifiers for the authenticated user."""
    user = request.db.query(User).get(userid)
    groups = [str(u) for u in user.groups]
    return groups

