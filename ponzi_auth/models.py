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
    def __init__(self, *args, **kw):
        # very necessary, even though superclass is object:
        super(Locatable, self).__init__(*args, **kw)
        self.__name__ = kw.get('name', None)
        self.__parent__ = kw.get('parent', None)

class KeyTraverser(object):
    """Map ``__getitem__`` (``self['key']``) to a SQLAlchemy query
    ``self.session.query(self.__model__).get(key)``
    
    :param session: SQLAlchemy session, stored as self.session."""
    def __init__(self, *args, **kw):
        # very necessary, even though superclass is object:
        super(KeyTraverser, self).__init__(*args, **kw)
        self.session = kw.get('session', None)

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
    __name__ = "users"
    __parent__ = None
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

    def __init__(self, *args, **kw):
        super(Users, self).__init__(*args, **kw)

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
    __name__ = u'passwordreset'
    __acl__ = [(Allow, Everyone, 'view')]
    __model__  = PasswordReset
    __child_acl__ = [(Allow, Everyone, 'view')]

    def __init__(self, *args, **kw):
        super(ForgotPassword, self).__init__(*args, **kw)
        self.session = kw.get('session')

class ExampleRoot(Locatable):
    __acl__ = [(Allow, Everyone, 'view')]
    def __init__(self, *args, **kw):
        """
        :param session: SQLAlchemy session
        :param children: dictionary of additional traversable objects
        """
        super(ExampleRoot, self).__init__(*args, **kw)
        self.traverse = {}
        self.traverse['passwordreset'] = ForgotPassword(parent=self)
        self.traverse['users'] = Users(parent=self)
        self.traverse.update(kw.get('children', {}))

    def __getitem__(self, key):
        return self.traverse[key]

def get_root(request):
    return ExampleRoot(name='', parent=None, session=request.db)

