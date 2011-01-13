from sqlalchemy import orm

import os
import sqlalchemy

import pyramid_formish
import pyramid_jinja2

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import NewRequest, BeforeRender

from stucco_auth import util
from stucco_auth import security
from stucco_auth import views, tables
from stucco_auth.tm import TM
from stucco_auth.interfaces import IAuthRoot

import stucco_evolution

from pyramid.security import authenticated_userid

import logging
log = logging.getLogger(__name__)

def new_request_listener(event):
    """Assign request.db and request.user as required by stucco_auth views"""
    event.request.db = event.request.environ['sqlalchemy.session']
    
def config(c):
    """Add stucco_auth views to Pyramid configurator instance."""
    c.add_view(name='login', context=IAuthRoot, renderer='login.html',
        permission='view')
    c.add_view(name='login', context=IAuthRoot, request_method='POST',
        permission='view')
    c.add_view(name='logout', context=IAuthRoot)

TEMPLATE_DIRS = ['stucco_auth:templates']

def init_settings(settings):
    from stucco_auth.models import get_root

    defaults = {
        'jinja2.directories': '\n'.join(TEMPLATE_DIRS),
    }

    defaults.update(settings) # overwrite defaults with values from settings
    settings.update(defaults) # merge defaults into settings

    engine = sqlalchemy.engine_from_config(settings)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)

    if not 'stucco_auth.db_engine' in settings:
        settings['stucco_auth.db_engine'] = engine

    if not 'stucco_auth.db_session_factory' in settings:
        settings['stucco_auth.db_session_factory'] = Session

def init_config(config, settings):
    config.add_renderer('.html', pyramid_jinja2.renderer_factory)
    config.scan('stucco_auth')

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

    session = settings['stucco_auth.db_session_factory']()
    
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

    authentication_policy = AuthTktAuthenticationPolicy(tkt_secret.value,
                                                callback=security.lookup_groups)

    authorization_policy = ACLAuthorizationPolicy()

    config = Configurator(root_factory=get_root,
                          settings=settings,
                          authentication_policy=authentication_policy,
                          authorization_policy=authorization_policy)
    init_config(config, settings)

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
