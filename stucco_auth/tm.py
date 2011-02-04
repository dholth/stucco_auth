
SESSION_KEY = 'sqlalchemy.session'


def get_session(request):
    """Return SQLAlchemy session for this request."""
    return request.environ[SESSION_KEY]


class TM(object):
    """Simple SQLAlchemy-only transaction manager."""
    def __init__(self, app, session_factory):
        self.session_factory = session_factory
        try:
            self.session_factory.remove
            self.removable = True
        except AttributeError:
            self.removable = False
        self.application = app

    def __call__(self, environ, start_response):
        environ[SESSION_KEY] = session = self.session_factory()
        try:
            result = self.application(environ, start_response)
            session.commit()
            return result
        except:
            session.rollback()
            raise
        finally:
            session.close()
            environ.pop(SESSION_KEY, None)
            if self.removable:
                self.session_factory.remove()


def make_tm(app, global_conf):
    """Attempt to work as paste-configured middleware. Look for a :param
    sqlalchemy.url: key and create a Session based on that key.

    Since the application probably needs the database during
    initialization, it will probably make more sense for the application
    to wrap itself in TM() rather than having paste do the job."""
    import sqlalchemy.orm
    Session = sqlalchemy.orm.sessionmaker(global_conf['sqlalchemy.url'])
    return TM(app, Session)
