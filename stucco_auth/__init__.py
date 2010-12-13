from sqlalchemy import orm

import os
import sqlalchemy

import pyramid_formish
import pyramid_jinja2

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.configuration import Configurator
from pyramid.events import NewRequest, BeforeRender

from stucco_auth import util
from stucco_auth import security
from stucco_auth import views, tables
from stucco_auth.tm import TM

import logging
log = logging.getLogger(__name__)

def assign_request_db(event):
    event.request.db = event.request.environ['sqlalchemy.session']

def add_get_flash(event):
    """Make get_flash available to the renderer when set as a
    pyramid.events.BeforeRender subscriber."""
    event['get_flash'] = util.get_flash

TEMPLATE_DIRS = ['stucco_auth:templates']

def init_settings(settings):
    from stucco_auth.models import get_root

    settings.setdefault('stucco_auth.allow_signup', False)
    settings.setdefault('stucco_auth.allow_password_reset', False) # not implemented yet
    settings.setdefault('jinja2.directories', '\n'.join(TEMPLATE_DIRS))
    settings.setdefault('stucco_auth.db_connect_string', 'sqlite:///stucco_auth.db')
    settings.setdefault('stucco_auth.db_engine',
                        sqlalchemy.create_engine(settings['stucco_auth.db_connect_string']))
    settings.setdefault('stucco_auth.db_session_factory',
                        orm.sessionmaker(bind=settings['stucco_auth.db_engine']))

def init_config(config, settings):
    config.load_zcml('stucco_auth:configure.zcml')

    config.add_renderer('.html', pyramid_jinja2.renderer_factory)
    config.add_renderer('.txt', pyramid_jinja2.renderer_factory)
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
    tables.initialize(session)
    tables.upgrade(session) # XXX or as something like `manage.py upgrade`

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
    config.add_subscriber(assign_request_db, NewRequest)
    
    config.add_subscriber(add_get_flash, BeforeRender)

    app = config.make_wsgi_app()
    tm = TM(app, settings['stucco_auth.db_session_factory'])

    # For pshell compatibility:
    tm.registry, tm.threadlocal_manager, tm.root_factory = \
            app.registry, app.threadlocal_manager, app.root_factory

    # In case database work was done during init:
    session.commit()

    return tm
