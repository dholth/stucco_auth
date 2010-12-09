"""
Traversal models.


In this package, 'session' or 'self.session' is always a SQLAlchemy
session. The Beaker session, if used, is always called
'request.session'. Apologies.
"""

import copy

from pyramid.security import Allow, Everyone, DENY_ALL

from stucco_auth.tables import User, PasswordReset

class Locatable(object):
    """Set ``self.__name__`` and ``self.__parent__`` from keyword
    arguments ``name`` and ``parent``."""
    __name__ = None
    __parent__ = None
    def __init__(self, name=None, parent=None):
        if name:
            self.__name__ = name
        if parent:
            self.__parent__ = parent

class KeyTraverser(object):
    """Map ``__getitem__`` (``self['key']``) to a SQLAlchemy query
    ``self.session.query(self.__model__).get(key)``
    
    :param session: SQLAlchemy session, stored as self.session."""
    def __init__(self, session=None):
        self.session = session

    def __getitem__(self, key):
        session = self.session
        item = session.query(self.__model__).get(key)
        if item is None:
            raise KeyError(key)
        item.__parent__ = self
        item.__name__ = unicode(key)
        if hasattr(self, '__child_acl__'):
            item.__acl__ = copy.copy(self.__child_acl__)
        return item

class Users(Locatable, KeyTraverser):
    __model__ = User
    __acl__ = [
            (Allow, 'group:admin', 'view'),
            (Allow, 'group:admin', 'post'),
            # In my application, I only allow admins to view the list
            # of all users, but individuals can still get to their own
            # User page. Let all logged in users view:
            (Allow, 'system.Authenticated', 'view'),
            DENY_ALL 
            ]
    __child_acl__ = [
            (Allow, 'group:admin', 'view'),
            (Allow, 'group:admin', 'post'),
            ]

    def __init__(self, name='users', parent=None, session=None):
        Locatable.__init__(self, name=name, parent=parent)
        KeyTraverser.__init__(self, session=session)

    def __iter__(self):
        query = self.session.query(User)
        return iter(query)

    def __getitem__(self, key):
        item = KeyTraverser.__getitem__(self, key)

        item.__acl__.extend([
            (Allow, item.user_id, 'view'),
            (Allow, item.user_id, 'post'),
            DENY_ALL])

        return item

class ForgotPassword(Locatable, KeyTraverser):
    __acl__ = [(Allow, Everyone, 'view')]
    __model__  = PasswordReset
    __child_acl__ = [(Allow, Everyone, 'view')]

    def __init__(self, name='passwordreset', parent=None, session=None):
        Locatable.__init__(self, name=name, parent=parent)
        KeyTraverser.__init__(self, session=session)

class DictTraverser(Locatable):
    traverse = None

    def __init__(self, name=None, parent=None):
        Locatable.__init__(self, name=name, parent=parent)
        self.traverse = {}

    def __getitem__(self, key):
        return self.traverse[key]

class AuthRoot(DictTraverser):
    __acl__ = [(Allow, Everyone, 'view'),
            (Allow, Everyone, 'sign-up')]
    def __init__(self, name=None, parent=None, session=None):
        """
        :param session: SQLAlchemy session
        """
        super(AuthRoot, self).__init__(name=name, parent=parent)
        self.traverse['passwordreset'] = ForgotPassword(parent=parent, session=session)
        self.traverse['users'] = Users(parent=parent, session=session)

class DefaultRoot(DictTraverser):
    __acl__ = [(Allow, Everyone, 'view')]

    def __init__(self, name=None, parent=None, session=None):
        """
        :param session: SQLAlchemy session
        """
        super(DefaultRoot, self).__init__(name=name, parent=parent)
        self.traverse['auth'] = AuthRoot(name='auth', parent=self,
                                         session=session)


def get_root(request):
    # XXX must explicitly dispose of session at end of request:
    session = None
    if request:
        session = request.db
    return DefaultRoot(name='', parent=None, session=session)
