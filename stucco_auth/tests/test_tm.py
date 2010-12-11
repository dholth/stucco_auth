import stucco_auth.tm

def test_make_tm():
    tm = stucco_auth.tm.make_tm(None, {'sqlalchemy.url':'sqlite:///:memory:'})
    assert isinstance(tm, stucco_auth.tm.TM)

def test_get_session():
    class MockRequest(object): pass
    request = MockRequest()
    request.environ = {stucco_auth.tm.SESSION_KEY:'session'}
    assert stucco_auth.tm.get_session(request) == 'session'

def build_mocks():
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

    return session, session_factory

def test_tm_0():
    session, session_factory = build_mocks()

    def app(environ, start_response):
        assert stucco_auth.tm.SESSION_KEY in environ

    tm = stucco_auth.tm.TM(app, session_factory)
    tm({}, None)
    assert session[0].committed
    assert session[0].closed
    assert not hasattr(session[0], 'rolledback')

def test_tm_1():
    session, session_factory = build_mocks()

    def app2(environ, start_response):
        raise Exception()

    tm2 = stucco_auth.tm.TM(app2, session_factory)
    try:
        tm2({}, None)
    except Exception:
        assert session[0].rolledback
        assert session[0].closed
        assert not hasattr(session[0], 'committed')

def test_tm_2():
    session = build_mocks()[0]

    def app(environ, start_response):
        assert stucco_auth.tm.SESSION_KEY in environ

    class RemovableSessionFactory(object):
        def __call__(self):
            return session[0]
        def remove(self):
            self.removed = True
    
    tm3 = stucco_auth.tm.TM(app, RemovableSessionFactory())
    tm3({}, None)
    assert tm3.session_factory.removed

