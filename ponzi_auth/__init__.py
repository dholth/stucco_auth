from sqlalchemy import orm

import os
import sqlalchemy

from ponzi_auth import views, tables
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.configuration import Configurator
from pyramid.events import NewRequest

import pyramid_formish
import pyramid_jinja2

from ponzi_auth import security
from ponzi_auth.tm import TM

import logging
logger = logging.getLogger(__name__)

def assign_request_db(event):
    event.request.db = event.request.environ['sqlalchemy.session']

TEMPLATE_DIRS = ['ponzi_auth:templates']

def init_settings(settings):
    from ponzi_auth import tables, security
    from ponzi_auth.models import get_root

    settings.setdefault('ponzi_auth.allow_signup', False)
    settings.setdefault('ponzi_auth.allow_password_reset', False) # not implemented yet
    settings.setdefault('jinja2.directories', '\n'.join(TEMPLATE_DIRS))
    settings.setdefault('ponzi_auth.db_connect_string', 'sqlite:///ponzi_auth.db')
    settings.setdefault('ponzi_auth.db_engine',
                        sqlalchemy.create_engine(settings['ponzi_auth.db_connect_string']))
    settings.setdefault('ponzi_auth.db_session_factory',
                        orm.sessionmaker(bind=settings['ponzi_auth.db_engine']))

def init_config(config, settings):
    config.load_zcml('ponzi_auth:configure.zcml')

    config.add_renderer('.html', pyramid_jinja2.renderer_factory)
    config.add_renderer('.txt', pyramid_jinja2.renderer_factory)
    config.scan('ponzi_auth')

    # Configure beaker session:
    import pyramid_beaker
    session_factory = pyramid_beaker.session_factory_from_settings(settings)
    config.set_session_factory(session_factory)


def main(global_config=None, **settings):
    """Return a Pyramid WSGI application."""
    if global_config is None:
        global_config = {}
    settings = dict(settings)
    init_settings(settings)

    session = settings['ponzi_auth.db_session_factory']()
    tables.initialize(session)
    tables.upgrade(session) # XXX or as something like `manage.py upgrade`

    # Retrieve stored auth_tkt secret, or make and store a secure new one:
    tkt_secret = session.query(tables.Settings).get('auth_tkt_secret')
    if tkt_secret is None:
        tkt_secret = tables.Settings(key='auth_tkt_secret', 
                value=os.urandom(20).encode('hex'))
        logger.debug("New auth_tkt secret: %s", tkt_secret.value)
        session.add(tkt_secret)

    authentication_policy = AuthTktAuthenticationPolicy(tkt_secret.value,
                                                        callback=security.lookup_groups)

    authorization_policy = ACLAuthorizationPolicy()

    config = Configurator(root_factory=get_root,
                          settings=settings,
                          authentication_policy=authentication_policy,
                          authorization_policy=authorization_policy)
    init_config(config, settings)

    # event handler will only work if ponzi_auth.tm is being used
    config.add_subscriber(assign_request_db, NewRequest)
    app = config.make_wsgi_app()
    tm = TM(app, settings['ponzi_auth.db_session_factory'])

    # For pshell compatibility:
    tm.registry, tm.threadlocal_manager, tm.root_factory = \
            app.registry, app.threadlocal_manager, app.root_factory
    from ponzi_auth.models import get_root

    # In case database work was done during init:
    session.commit()

    return tm
