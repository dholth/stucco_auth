import sqlalchemy.orm.exc
from stucco_auth.tables import User

def lookup_groups(authenticated_userid, request):
    """Return a list of group identifiers for the current user (or []
    if no one is logged in)
    
    Called by the authentication policy. View code can use
    pyramid.security.effective_principals(request)"""
    return [str(g) for g in request.user.groups]

def authenticate(session, username, password):
    """Return User() or None if username not found / invalid password.
    
    :param session: SQLAlchemy session."""
    try:
        u = session.query(User).filter(User.username==username).one()
        if u.check_password(password):
            u.last_login = sqlalchemy.func.current_timestamp()
            return u
    except sqlalchemy.orm.exc.NoResultFound:
        pass
    return None

