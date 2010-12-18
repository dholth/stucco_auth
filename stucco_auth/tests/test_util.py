from stucco_auth.util import Flasher

def test_flash():
    class MockRequest(object): pass
    class DummySession(dict): # XXX which is it? a mock? or a dummy?
        def save(self): pass
        invalidate = delete = save
    MockRequest.session = DummySession()
    request = MockRequest()
    flasher = Flasher(request)
    assert flasher.messages == []
    flasher.add('Gordon!')        
    flasher.add('Flash!')
    output = [x.text for x in flasher.pop_iter()]
    assert output == ['Flash!', 'Gordon!'], output
    assert flasher.messages == []
