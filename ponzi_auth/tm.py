
class TM(object):
    """Simple SQLAlchemy-only transaction manager."""
    def __init__(self, app, session_factory):
        self.session_factory = session_factory
        try:
            session_factory.remove
            self.removable = True
        except AttributeError:
            self.removable = False
        self.application = app

    def __call__(self, environ, start_response):
        try:
            environ['sqlalchemy.session'] = session_factory()
            result = self.application(environ, start_response)
            environ['sqlalchemy.session'].commit()
            return result
        except:
            environ['sqlalchemy.session'].rollback()
            raise
        finally:
            environ['sqlalchemy.session'].close()
            if self.removable:
                self.session_factory.remove()

def make_tm(app, global_conf):
    return TM(app, global_conf['sqlalchemy.session_factory'])

