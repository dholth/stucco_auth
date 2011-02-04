
def test_locatable():
    from stucco_auth.models import Locatable

    l = Locatable(name='users', parent='parent')
    assert l.__name__ == 'users'
    assert l.__parent__ == 'parent'
    
    l = Locatable(name='', parent='')
    assert l.__name__ is None # not sure if this is the correct behavior.
    assert l.__parent__ is None


def test_get_root():
    import stucco_auth.models
    assert stucco_auth.models.get_root(None) is not None
    