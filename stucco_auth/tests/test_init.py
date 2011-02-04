from nose.tools import raises
import pyramid.exceptions

def test_demo_app():
    """Test demo WSGI app creation function."""
    import stucco_auth
    config = {'default_locale_name': 'en', 'sqlalchemy.url': 'sqlite:///:memory:', 'debug_authorization': 'false', 'jinja2.directories': 'stucco_auth:templates', 'debug_templates': 'true', 'reload_templates': 'true', 'debug_notfound': 'false'} 
    assert stucco_auth.demo_app({}, **config) is not None

def test_request_listener():
    """Assert new_request_listener assigns request.db from WSGI environment."""
    import stucco_auth.tm
    class Dummy(object): pass
    event = Dummy()
    event.request = Dummy()
    event.request.environ = {}
    event.request.environ[stucco_auth.tm.SESSION_KEY] = 14
    stucco_auth.new_request_listener(event)
    assert event.request.db == 14

@raises(pyramid.exceptions.ConfigurationError)
def test_authentication_policy_required():
    """Assert stucco_auth views raise error if AuthenticationPolicy is not
    installed. Login/logout views will not do much good if it is impossible
    to actually log in and out.""" 
    import pyramid.config
    import stucco_auth
    config = pyramid.config.Configurator()
    config.include(stucco_auth.config_views)
    
def test_includeme():
    import pyramid.config
    import stucco_auth
    config = pyramid.config.Configurator()
    config.testing_securitypolicy()
    config.include(stucco_auth.includeme)
    
