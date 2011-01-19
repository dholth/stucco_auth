import unittest
import sqlalchemy.orm
import stucco_auth.views 
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.testing import DummyRequest
from sqlalchemy.orm.exc import NoResultFound
from stucco_auth.tables import Group


class TableTests(unittest.TestCase):
    def setUp(self):
        engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=False)
        self.Session = sqlalchemy.orm.sessionmaker(bind=engine)
        session = self.Session()
        
        import stucco_evolution
        stucco_evolution.initialize(session)
        stucco_evolution.create_or_upgrade_packages(session, 'stucco_auth')
        session.commit()

    def test_user(self):
        user = stucco_auth.tables.User(username='alice',
            first_name='Alice', last_name='Liddell',
            email='alice@example.org')
        
        str(user) # User can str() when user_id is None?

        session = self.Session()
        session.add(user)
        session.flush()
        
        self.assertEqual(user.is_anonymous(), False)
        assert str(user).startswith('user:'), 'str(user) must start with user:'
        
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

    def test_view_model(self):
        assert stucco_auth.views.view_model(None) == {}

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

    def test_login(self):
        d = stucco_auth.views.login(self.request)
        self.assertEqual(d['status_type'], u'')

    def test_post_login(self):
        self.request.method = 'POST'
        self.request.params['form.submitted'] = True
        self.request.params['username'] = 'user1'
        self.request.params['password'] = 'user1'
        self.request.referrer = 'http://www.example.org/'

        class User(stucco_auth.tables.AnonymousUser):
            def check_password(self, p):
                return True

        self.db_session.add(User())
        d = stucco_auth.views.login_post(self.request)
        self.assertTrue(isinstance(d, HTTPFound), type(d))

    def test_logout(self):
        d = stucco_auth.views.logout(self.request)
        self.assertTrue(isinstance(d, HTTPFound))

    def test_lookup_groups(self):
        user = stucco_auth.tables.User()
        user.groups.append(stucco_auth.tables.Group(name='agroup'))
        self.db_session.data = [user]
        assert 'group:agroup' in stucco_auth.security.lookup_groups(user.user_id, self.request)

        self.db_session.data = [None]
        assert stucco_auth.security.lookup_groups(4, self.request) is None

    def test_authenticate(self):
        import stucco_evolution
        import stucco_auth.security
        # Very accurate mock session:
        Session = sqlalchemy.orm.sessionmaker(
            sqlalchemy.create_engine('sqlite:///:memory:')
            )
        session = Session()
        stucco_evolution.manager(session, 'stucco_auth').create()
        user = stucco_auth.security.authenticate(session, 'foo', 'bar')
        assert user is None, user
        
