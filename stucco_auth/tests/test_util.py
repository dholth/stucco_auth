from stucco_auth.util import get_flash, set_flash

def test_flash():
    class MockRequest(object): pass
    class DummySession(dict): # XXX which is it? a mock? or a dummy?
        def save(self): pass
        invalidate = delete = save
    MockRequest.session = DummySession()
    request = MockRequest()
    assert get_flash(request) == []        
    set_flash(request, 'Flash!')    
    set_flash(request, 'Gordon!')
    assert get_flash(request) == ['Flash!', 'Gordon!']
    assert get_flash(request) == []
    