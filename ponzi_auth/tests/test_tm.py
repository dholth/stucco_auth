import ponzi_auth.tm

def test_make_tm():
    tm = ponzi_auth.tm.make_tm(None, {'sqlalchemy.url':'sqlite:///:memory:'})
    assert isinstance(tm, ponzi_auth.tm.TM)

def test_get_session():
    class MockRequest(object): pass
    request = MockRequest()
    request.environ = {ponzi_auth.tm.SESSION_KEY:'session'}
    assert ponzi_auth.tm.get_session(request) == 'session'

def test_tm():
    class MockSession(object):
        def commit(self):
            self.committed = True
        def rollback(self):
            self.rolledback = True
        def close(self):
            self.closed = True

    session = [MockSession()]
    def session_factory():
        return session[0]

    def app(environ, start_response):
        assert ponzi_auth.tm.SESSION_KEY in environ

    tm = ponzi_auth.tm.TM(app, session_factory)
    tm({}, None)
    assert session[0].committed
    assert session[0].closed
    assert not hasattr(session[0], 'rolledback')


    session[0] = MockSession()
    def app2(environ, start_response):
        raise Exception()
    tm2 = ponzi_auth.tm.TM(app2, session_factory)
    try:
        tm2({}, None)
    except Exception:
        assert session[0].rolledback
        assert session[0].closed
        assert not hasattr(session[0], 'committed')


    class RemovableSessionFactory(object):
        def __call__(self):
            return session[0]
        def remove(self):
            self.removed = True
    
    tm3 = ponzi_auth.tm.TM(app, RemovableSessionFactory())
    tm3({}, None)
    assert tm3.session_factory.removed

