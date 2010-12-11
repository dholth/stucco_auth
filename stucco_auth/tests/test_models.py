from nose.tools import raises

def test_keytraverser():
    from pyramid.security import DENY_ALL
    from stucco_auth.models import KeyTraverser

    class Contained(object):
        pass

    class Container(KeyTraverser):
        __model__ = Contained
        __child_acl__ = [DENY_ALL]

    class MockSession(object):
        def query(self, model):
            return self
        def get(self, key):
            if key == 1:
                return Contained()
            else:
                return None

    assert Container(
            session=MockSession()
            )[1].__acl__ == Container.__child_acl__

    @raises(KeyError)
    def raise_keyerror():
        Container(session=MockSession())[2]
    raise_keyerror()

def test_list_user():
    from stucco_auth.models import Users

    class MockSession(list):
        def query(self, model):
            return self

    u = Users(session=MockSession(range(10)))
    assert list(u) == range(10)

def test_traverse_users():
    from stucco_auth.models import Users
    class MockUser(object):
        user_id = 4
    class MockSession(list):
        def query(self, model):
            return self
        def get(self, model):
            return MockUser()
    u = Users(session=MockSession(), name='users', parent='parent')
    assert len(u[4].__acl__) > len(u.__child_acl__), \
        """Users.__getitem__ did not extend copy of __child_acl__ with per-user permissions."""

def test_locatable():
    from stucco_auth.models import Locatable

    l = Locatable(name='users', parent='parent')
    assert l.__name__ == 'users'
    assert l.__parent__ == 'parent'
    
    l = Locatable(name='', parent='')
    assert l.__name__ is None # not sure if this is the correct behavior.
    assert l.__parent__ is None

def test_scripting_session():
    # pshell compatibility hack to create a SQLALchemy session in get_root() if
    # middleware did not set any.
    from stucco_auth.models import get_root
    class Bag: pass
    class MockRequest:
        registry = Bag()
        registry.settings = {'stucco_auth.db_session_factory':list}
    get_root(MockRequest)
    assert isinstance(MockRequest.db, list), MockRequest.db
    