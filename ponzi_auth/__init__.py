import sqlalchemy
from sqlalchemy import orm

import pyramid_formish

from pyramid.events import NewRequest
from pyramid.configuration import Configurator
import pyramid_jinja2
from ponzi_auth import views

def assign_request_db(event):
    request = event.request
    views.get_dbsession(request) # assigns request.db as a side effect. XXX this is lame

def main(global_config=None, **settings):
    """Return a Pyramid WSGI application."""

    import ponzi_auth.tables
    from ponzi_auth.models import get_root

    if global_config is None:
        global_config = {}
    settings = dict(settings)
    settings.setdefault('jinja2.directories', 'ponzi_auth:templates')
    settings.setdefault('ponzi_auth.allow_signup', False)
    settings.setdefault('ponzi_auth.allow_password_reset', False) # not implemented yet
    settings.setdefault('ponzi_auth.db_connect_string', 'sqlite:///ponzi_auth.db')
    settings.setdefault('ponzi_auth.db_engine',
                        sqlalchemy.create_engine(settings['ponzi_auth.db_connect_string']))
    settings.setdefault('ponzi_auth.db_session_factory',
                        orm.sessionmaker(bind=settings['ponzi_auth.db_engine'],
                                         autocommit=False,
                                         autoflush=False))

    config = Configurator(root_factory=get_root, settings=settings)

    config.load_zcml('ponzi_auth:configure.zcml')

    session = settings['ponzi_auth.db_session_factory']()
    ponzi_auth.tables.initialize(session)
    ponzi_auth.tables.upgrade(session) # XXX or as something like `manage.py upgrade`
    session.commit()

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

    return config.make_wsgi_app()

