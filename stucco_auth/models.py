"""
Traversal models.
"""

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

    def __init__(self, name=None, parent=None):
        Locatable.__init__(self, name=name, parent=parent)


def get_root(request):
    return DefaultRoot(name='', parent=None)
