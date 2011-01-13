import os
import sqlalchemy

import pyramid_jinja2

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import NewRequest

from stucco_auth import security
from stucco_auth import tables
from stucco_auth import views
from stucco_auth.tm import TM, SESSION_KEY
from stucco_auth.interfaces import IAuthRoot

import logging
log = logging.getLogger(__name__)


def new_request_listener(event):
    """Assign request.db as required by stucco_auth views"""
    # XXX 'fetch current session' should be configurable based on what kind of
    # transaction manager is in use, etc. For a scoped session, this might be
    # event.request.db = myapp.models.DBSession(), or the session for this
    # request might have been already instantiated into the wsgi environ by
    # a custom transaction manager.
    event.request.db = event.request.environ[SESSION_KEY]


def config(c):
    """Add stucco_auth views to Pyramid configurator instance."""
    c.add_view(views.login, name='login', context=IAuthRoot, renderer='login.html',
        permission='view')
    c.add_view(views.login_post, name='login', context=IAuthRoot, request_method='POST',
        permission='view')
    c.add_view(views.logout, name='logout', context=IAuthRoot)
    c.add_static_view('static', 'stucco_auth:static')

TEMPLATE_DIRS = ['stucco_auth:templates']


def init_settings(settings):
    defaults = {
        'jinja2.directories': '\n'.join(TEMPLATE_DIRS),
    }

    defaults.update(settings)  # overwrite defaults with values from settings
    settings.update(defaults)  # merge defaults into settings

    engine = sqlalchemy.engine_from_config(settings)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)

    if not 'stucco_auth.db_engine' in settings:
        settings['stucco_auth.db_engine'] = engine

    if not 'stucco_auth.db_session_factory' in settings:
        settings['stucco_auth.db_session_factory'] = Session


def init_config(config, settings):
    config.add_renderer('.html', pyramid_jinja2.renderer_factory)

    config.include('stucco_auth.config')

    # Configure beaker session:
    import pyramid_beaker
    session_factory = pyramid_beaker.session_factory_from_settings(settings)
    config.set_session_factory(session_factory)


def main(global_config=None, **settings):
    """Return a Pyramid WSGI application."""    
    from stucco_auth.models import get_root

    if global_config is None:
        global_config = {}
        
    settings = dict(settings)
    init_settings(settings)

    Session = settings['stucco_auth.db_session_factory']
    session = Session()

    import stucco_evolution
    stucco_evolution.initialize(session)

    stucco_evolution.create_or_upgrade_many(
        stucco_evolution.managers(session,
            stucco_evolution.dependencies('stucco_auth')))

    # Retrieve stored auth_tkt secret, or make and store a secure new one:
    tkt_secret = session.query(tables.Settings).get('auth_tkt_secret')
    if tkt_secret is None:
        tkt_secret = tables.Settings(key='auth_tkt_secret',
                value=os.urandom(20).encode('hex'))
        log.info("New auth_tkt secret: %s", tkt_secret.value)
        session.add(tkt_secret)

    authentication_policy = AuthTktAuthenticationPolicy(
        tkt_secret.value, callback=security.lookup_groups)

    authorization_policy = ACLAuthorizationPolicy()

    config = Configurator(root_factory=get_root,
                          settings=settings,
                          authentication_policy=authentication_policy,
                          authorization_policy=authorization_policy)
    init_config(config, settings)
    
    config.add_view(context=IAuthRoot, renderer='welcome.html')

    # event handler will only work if stucco_auth.tm is being used
    config.add_subscriber(new_request_listener, NewRequest)

    app = config.make_wsgi_app()
    tm = TM(app, settings['stucco_auth.db_session_factory'])

    # For pshell compatibility:
    tm.registry, tm.threadlocal_manager, tm.root_factory = \
            app.registry, app.threadlocal_manager, app.root_factory

    # In case database work was done during init:
    session.commit()

    return tm
