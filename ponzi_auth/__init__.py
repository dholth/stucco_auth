from pyramid.configuration import Configurator
from ponzi_auth.models import get_root

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=get_root, settings=settings)
    config.begin()
    config.add_view('ponzi_auth.views.my_view',
                    context='ponzi_auth.models.MyModel',
                    renderer='ponzi_auth:templates/mytemplate.pt')
    config.add_static_view('static', 'ponzi_auth:static')
    config.end()
    return config.make_wsgi_app()

