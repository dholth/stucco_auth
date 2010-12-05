from ponzi_auth.tables import User

def lookup_groups(userid, request):
    user = request.db.query(User).get(userid)
    groups = [str(u) for u in user.groups]
    return groups

