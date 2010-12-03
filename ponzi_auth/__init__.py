from pyramid.configuration import Configurator
from ponzi_auth.models import get_root


def main(global_config, **settings):
    """Return a Pyramid WSGI application."""
    config = Configurator(root_factory=get_root, settings=settings)
    config.begin()    
    from pyramid_jinja2 import renderer_factory
    config.add_renderer('.jinja2', renderer_factory)
    config.add_view('ponzi_auth.views.my_view',
                    context='ponzi_auth.models.MyModel',
                    renderer='ponzi_auth:templates/mytemplate.pt')
    config.add_static_view('static', 'ponzi_auth:static')
    config.end()
    return config.make_wsgi_app()
