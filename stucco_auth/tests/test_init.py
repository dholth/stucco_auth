
def test_main():
    """Test demo WSGI app creation function."""
    import stucco_auth
    config = {'default_locale_name': 'en', 'sqlalchemy.url': 'sqlite:///:memory:', 'debug_authorization': 'false', 'jinja2.directories': 'stucco_auth:templates', 'debug_templates': 'true', 'reload_templates': 'true', 'debug_notfound': 'false'} 
    stucco_auth.main({}, **config)

def test_request_listener():
    """Assert new_request_listener assigns request.db from WSGI environment."""
    import stucco_auth
    import stucco_auth.tm
    class Dummy(object): pass
    event = Dummy()
    event.request = Dummy()
    event.request.environ = {}
    event.request.environ[stucco_auth.tm.SESSION_KEY] = 14
    stucco_auth.new_request_listener(event)
    assert event.request.db == 14
    