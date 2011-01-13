"""
Traversal models.
"""

import warnings
from zope.interface import implements
from pyramid.security import Allow, Everyone

from stucco_auth.interfaces import IAuthRoot

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

class DefaultRoot(dict, Locatable):
    implements(IAuthRoot)

    __acl__ = [(Allow, Everyone, 'view')]

    def __init__(self, name=None, parent=None, db=None):
        """
        :param db: SQLAlchemy db
        """
        Locatable.__init__(self, name=name, parent=parent)
        self.db = db

def get_root(request):
    db = None
    try:
        db = request.db
    except AttributeError:
        # For proper transaction and db lifecycle management, the 
        # SQLAlchemy db should be created in middleware and assigned to 
        # request.db in a callback or a custom request factory.
        warnings.warn(
            "get_root() created SQLAlchemy.db"
            " (only o.k. for scripting i.e. pshell)",
            RuntimeWarning)
        db = request.registry.settings['stucco_auth.db_session_factory']()
        request.db = db
    return DefaultRoot(name='', parent=None, db=db)

