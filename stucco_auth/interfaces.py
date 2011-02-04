from zope.interface import Interface


class IAuthRoot(Interface):
    """To hang stucco_auth views off an arbitrary class, write

    from zope.interface import implements
    from stucco_auth.interfaces import IAuthRoot

    class MyRoot(object):
        implements(IAuthRoot)
    """
