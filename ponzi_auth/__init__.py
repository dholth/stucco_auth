import sqlalchemy
from sqlalchemy import orm

from pyramid.configuration import Configurator
from pyramid_jinja2 import renderer_factory

from ponzi_auth.models import get_root


def main(global_config=None, **settings):
    """Return a Pyramid WSGI application."""

    if global_config is None:
        global_config = {}
    settings = dict(settings)
    settings.setdefault('jinja2.directories', 'ponzi_auth:templates')
    settings.setdefault('ponzi_auth.allow_signup', False)
    settings.setdefault('ponzi_auth.db_connect_string', 'sqlite:///ponzi_auth.db')
    settings.setdefault('ponzi_auth.db_engine',
                        sqlalchemy.create_engine(settings['ponzi_auth.db_connect_string']))
    settings.setdefault('ponzi_auth.db_session_factory',
                        orm.sessionmaker(bind=settings['ponzi_auth.db_engine'],
                                         autocommit=False,
                                         autoflush=False))

    config = Configurator(root_factory=get_root, settings=settings)
    config.add_renderer('.html', renderer_factory)
    config.scan('ponzi_auth')
    config.add_static_view('static', 'ponzi_auth:static')
    return config.make_wsgi_app()
