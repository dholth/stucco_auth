import sqlalchemy
from sqlalchemy import orm

from ponzi_auth import views, tables
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.configuration import Configurator
from pyramid.events import NewRequest

import pyramid_formish
import pyramid_jinja2

from ponzi_auth.security import find_groups


def assign_request_db(event):
    request = event.request
    views.get_dbsession(request) # assigns request.db as a side effect. XXX this is lame

TEMPLATE_DIRS = ['ponzi_auth:templates']

def init_settings(settings):
    settings.setdefault('jinja2.directories', TEMPLATE_DIRS[0])
    settings.setdefault('ponzi_auth.db_connect_string', 'sqlite:///ponzi_auth.db')
    settings.setdefault('ponzi_auth.db_engine',
                        sqlalchemy.create_engine(settings['ponzi_auth.db_connect_string']))
    settings.setdefault('ponzi_auth.db_session_factory',
                        orm.sessionmaker(bind=settings['ponzi_auth.db_engine'],
                                         autocommit=False,
                                         autoflush=False))
    settings.setdefault('ponzi_auth.allow_signup', False)
    settings.setdefault('ponzi_auth.allow_password_reset', False) # not implemented yet

def init_config(config, settings):
    config.load_zcml('ponzi_auth:configure.zcml')

    session = settings['ponzi_auth.db_session_factory']()
    tables.initialize(session)
    tables.upgrade(session) # XXX or as something like `manage.py upgrade`
    session.flush()

    session = settings['ponzi_auth.db_session_factory']()
    
    config.add_subscriber(assign_request_db, NewRequest)

    config.add_renderer('.html', pyramid_jinja2.renderer_factory)
    config.add_renderer('.txt', pyramid_jinja2.renderer_factory)
    config.scan('ponzi_auth')

    # configure beaker session
    import pyramid_beaker
    session_factory = pyramid_beaker.session_factory_from_settings(settings)
    config.set_session_factory(session_factory)

    # find the pyramid_uniform templates instead of the pyramid_formish templates:
    import zope
    from pkg_resources import resource_filename
    sm = zope.component.getSiteManager()
    sm.registerUtility([resource_filename('pyramid_uniform', 'templates/zpt')],
            pyramid_formish.IFormishSearchPath)


def main(global_config=None, **settings):
    """Return a Pyramid WSGI application."""

    import ponzi_auth.tables
    from ponzi_auth.models import get_root

    if global_config is None:
        global_config = {}
    settings = dict(settings)
    init_settings(settings)
    authentication_policy = AuthTktAuthenticationPolicy('oursecret',
                                                        callback=find_groups)
    authorization_policy = ACLAuthorizationPolicy()
    config = Configurator(root_factory=get_root,
                          settings=settings,
                          authentication_policy=authentication_policy,
                          authorization_policy=authorization_policy)
    init_config(config, settings)
    return config.make_wsgi_app()
