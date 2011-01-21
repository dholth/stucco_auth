from nose.tools import raises

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
    