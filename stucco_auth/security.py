import sqlalchemy
from stucco_auth.tables import User


def lookup_groups(userid, request):
    """Return a list of group identifiers for the current user (or []
    if no one is logged in)

    Called by the authentication policy. View code can use
    pyramid.security.effective_principals(request)"""
    user = request.db.query(User).get(userid)
    if user:
        return [str(g) for g in user.groups]
    return None


def authenticate(session, username, password):
    """Return User() or None if username not found / invalid password.

    :param session: SQLAlchemy session."""
    u = session.query(User).filter(User.username == username).first()
    if u and u.check_password(password):
        u.last_login = sqlalchemy.func.current_timestamp()
        return u
    return None
