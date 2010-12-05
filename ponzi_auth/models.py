"""
Traversal models.


In this package, 'session' or 'self.session' is always a SQLAlchemy
session. The Beaker session, if used, is always called
'request.session'. Apologies.
"""

from pyramid.security import Allow, Everyone, DENY_ALL

from ponzi_auth.tables import User, PasswordReset

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
            item.__acl__ = self.__child_acl__.copy()
        return item

class Users(Locatable, KeyTraverser):
    __model__ = User
    __acl__ = [
            (Allow, 'group:admin', 'view'),
            (Allow, 'group:admin', 'post'),
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

class ExampleRoot(Locatable):
    __acl__ = [(Allow, Everyone, 'view')]
    def __init__(self, name=None, parent=None, session=None, children={}):
        """
        :param session: SQLAlchemy session
        :param children: dictionary of additional traversable objects
        """
        Locatable.__init__(self, name=name, parent=parent)
        self.traverse = {}
        self.traverse['passwordreset'] = ForgotPassword(parent=self, session=session)
        self.traverse['users'] = Users(parent=self, session=session)
        self.traverse.update(children)

    def __getitem__(self, key):
        return self.traverse[key]

def get_root(request):
    # XXX must explicitly dispose of session at end of request:
    session = None
    if request:
        session = request.registry.settings['ponzi_auth.db_session_factory']()
    return ExampleRoot(name='', parent=None, session=session)

