import unittest

from stucco_auth.tables import Group

import sqlalchemy.orm
from cherrypy._cperror import HTTPRedirect


class TableTests(unittest.TestCase):
    def setUp(self):
        engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=False)
        self.Session = sqlalchemy.orm.sessionmaker(bind=engine)
        session = self.Session()
        stucco_auth.tables.initialize(session)

    def test_user(self):
        user = stucco_auth.tables.User(username='alice',
            first_name='Alice', last_name='Liddell',
            email='alice@example.org')

        self.assertEqual(user.is_anonymous(), False)
        self.assertEqual(str(user), 'user:alice')

        session = self.Session()
        session.add(user)        

        group = Group(name='Galois')

        user.groups.append(group)

        assert user in group.users
        assert group in user.groups

        group2 = Group(name='linear')
        group2.users.append(user)

        assert user in group2.users
        assert group2 in user.groups

    def test_password(self):
        user = stucco_auth.tables.User(is_active=True, password='*')
        assert user.check_password('anything') == False
        
        user.set_password('mimsy')
        assert user.check_password('mimsy')
        assert not user.check_password('borogroves')

        user.set_password('borogroves')
        assert user.check_password('borogroves')

        user.is_active = False
        assert not user.check_password('borogroves')

    def test_group(self):
        group = stucco_auth.tables.Group()
        group.name = 'testgroup'
        self.assertEqual(str(group), 'group:testgroup')

    def test_anonymous(self):
        user = stucco_auth.tables.AnonymousUser()
        self.assertTrue(user.is_anonymous())
        self.assertFalse(user.check_password('foo'))

    def test_password_reset(self):
        pr = stucco_auth.tables.PasswordReset()
        self.assertTrue(pr.isexpired())

    def test_view_plural(self):
        context = range(10)
        class MockRequest(object): pass
        request = MockRequest()
        request.context = context
        assert stucco_auth.views.view_plural(request)['items'] == list(context)

    def test_view_model(self):
        assert stucco_auth.views.view_model(None) == {}

import stucco_auth

# disabled for now
# class MainTests(unittest.TestCase):

#     def test_main(self):
#         settings = {'stucco_auth.db_session_factory': MockDBSession}
#         app = stucco_auth.main({}, **settings)
#         assert hasattr(app, 'registry')

from stucco_auth.models import get_root

class ModelsTests(unittest.TestCase):
    
    def test_get_root(self):
        class MockRequest:
            db = 'foo'
        root = get_root(MockRequest)
        assert root is not None
        assert root['auth']['users'].session is 'foo'

import stucco_auth.views 
from pyramid.testing import DummyRequest
from sqlalchemy.orm.exc import NoResultFound
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound

class MockEngine(object):
    pass

    # def has_table(self, t):
    #     return True
    #
    # def create(self, *args, **kwargs):
    #     pass

class MockDBSession(object):

    def __init__(self):
        self.data = []
        self.engine = MockEngine()

    def query(self, s):
        return self
    
    def filter(self, *args):
        return self
    
    def filter_by(self, **kwargs):
        return self

    def one(self):
        if len(self.data) == 0:
            raise NoResultFound()
        return self.data[0]

    def get(self, key):
        return self.data[0]

    def add(self, obj):
        self.data.append(obj)

    def count(self):
        return len(self.data)

    def commit(self):
        pass

    _marker = object()
    def bind(self, engine=_marker):
        if engine is not self._marker:
            self.engine = engine
        return self.engine
    bind = property(bind, bind)

class ViewsTests(unittest.TestCase):

    def setUp(self):
        class DummySession(dict):
            def save(self): pass
            invalidate = delete = save
        
        self.request = DummyRequest()
        self.request.relative_url = lambda x: x
        self.settings = self.request.registry.settings = {}
        self.db_session = MockDBSession()
        self.db_session.data = []
        self.request.db = self.db_session
        self.request.session = DummySession()
        self.settings['stucco_auth.db_session_factory'] = \
            lambda db_session=self.db_session: db_session

    def tearDown(self):
        pass

    def test_get_dbsession(self):
        self.assertTrue(isinstance(stucco_auth.views.get_dbsession(self.request),
                                   MockDBSession))

    def test_login(self):
        d = stucco_auth.views.login(self.request)
        self.assertEqual(d['status_type'], u'')

    def test_post_login(self):
        self.request.method = 'POST'
        self.request.params['form.submitted'] = True
        self.request.params['username'] = 'user1'
        self.request.params['password'] = 'user1'
        self.request.referrer = 'http://www.example.org/'
        
        # no more status_type, just a redirect (always)
        # d = stucco_auth.views.login_post(self.request)
        # self.assertEqual(d['status_type'], u'error')

        class User(stucco_auth.tables.AnonymousUser):
            def check_password(self, p):
                return True

        self.db_session.add(User())
        d = stucco_auth.views.login_post(self.request)
        self.assertTrue(isinstance(d, HTTPFound), type(d))

    def test_signup(self):
        # by default signup is disabled
        self.assertRaises(NotFound, lambda: stucco_auth.views.signup(self.request))

        self.settings['stucco_auth.allow_signup'] = True
        d = stucco_auth.views.signup(self.request)
        self.assertEqual(d['status_type'], u'')

    def test_post_signup(self):
        self.settings['stucco_auth.allow_signup'] = True
        self.request.method = 'POST'
        self.request.params['form.submitted'] = True
        self.request.params['username'] = 'user1'
        self.request.params['password'] = 'user1'
        self.request.params['firstname'] = 'foo'
        self.request.referrer = 'http://example.org/'

        # should successfully sign up and add a new user
        d = stucco_auth.views.signup(self.request)
        self.assertEqual(d['status_type'], u'info')

        # will fail because of creating with same username
        d = stucco_auth.views.signup(self.request)
        self.assertEqual(d['status_type'], u'error')

    def test_logout(self):
        d = stucco_auth.views.logout(self.request)
        self.assertTrue(isinstance(d, HTTPFound))

    # def test_find_user(self):
    #     d = stucco_auth.security.find_user(self.request)
    #     self.assertTrue(d is None)
    #     self.assertRaises(NoResultFound,
    #                       lambda: stucco_auth.security.find_user(self.request, 'foo'))

    def test_lookup_groups(self):
        user = stucco_auth.tables.User()
        user.groups.append(stucco_auth.tables.Group(name='agroup'))
        self.db_session.data = [user]
        assert 'group:agroup' in stucco_auth.security.lookup_groups(user.user_id, self.request)

        self.db_session.data = [None]
        assert stucco_auth.security.lookup_groups(4, self.request) == []
        # MockDBSession is not this smart. Could use sqlite:///:memory: instead...
        # self.assertEqual([], [x for x in find_groups(None, self.request)])
        # self.assertEqual([], [x for x in find_groups(user, self.request)])
        # self.assertRaises(NoResultFound,
        #                   lambda: self.assertEqual([], [x for x in find_groups('foo', self.request)]))
        
    def test_authenticate(self):
        import stucco_auth.security
        import stucco_auth.tables
        # Very accurate mock session:
        Session = sqlalchemy.orm.sessionmaker(
            sqlalchemy.create_engine('sqlite:///:memory:')
            )
        session = Session()
        stucco_auth.tables.Base.metadata.create_all(session.bind)
        user = stucco_auth.security.authenticate(session, 'foo', 'bar')
        assert user is None, user
        