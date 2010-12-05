import unittest

import ponzi_auth.tables
from ponzi_auth.tables import Group

import sqlalchemy
import sqlalchemy.orm

class TableTests(unittest.TestCase):
    def setUp(self):
        engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=False)
        self.Session = sqlalchemy.orm.sessionmaker(bind=engine)
        session = self.Session()
        ponzi_auth.tables.initialize(session)

    def test_user(self):
        user = ponzi_auth.tables.User(username='alice',
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
        user = ponzi_auth.tables.User(is_active=True, password='mimsy')
        assert user.check_password('mimsy')
        assert not user.check_password('borogroves')

        user.set_password('borogroves')
        assert user.check_password('borogroves')

        user.is_active = False
        assert not user.check_password('borogroves')

    def test_group(self):
        group = ponzi_auth.tables.Group()
        group.name = 'testgroup'
        self.assertEqual(str(group), 'group:testgroup')

    def test_anonymous(self):
        user = ponzi_auth.tables.AnonymousUser()
        self.assertTrue(user.is_anonymous())
        self.assertFalse(user.check_password('foo'))

    def test_password_reset(self):
        pr = ponzi_auth.tables.PasswordReset()
        self.assertTrue(pr.isexpired())


import ponzi_auth

class MainTests(unittest.TestCase):

    def test_main(self):
        app = ponzi_auth.main({})
        assert hasattr(app, 'registry')

from ponzi_auth.models import get_root

class ModelsTests(unittest.TestCase):
    
    def test_get_root(self):
        root = get_root(None)
        assert root is not None

import ponzi_auth.views 
from pyramid.testing import DummyRequest
from sqlalchemy.orm.exc import NoResultFound
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound

class MockDBSession(object):

    def __init__(self):
        self.data = []

    def query(self, s):
        return self

    def filter_by(self, **kwargs):
        return self

    def one(self):
        if len(self.data) == 0:
            raise NoResultFound()
        return self.data[0]

    def add(self, obj):
        self.data.append(obj)

    def count(self):
        return len(self.data)

    def commit(self):
        pass

class ViewsTests(unittest.TestCase):

    def setUp(self):
        self.request = DummyRequest()
        self.settings = self.request.registry.settings = {}
        self.db_session = MockDBSession()
        self.db_session.data = []
        self.settings['ponzi_auth.db_session_factory'] = \
            lambda db_session=self.db_session: db_session

    def tearDown(self):
        pass

    def test_get_dbsession(self):
        self.assertTrue(isinstance(ponzi_auth.views.get_dbsession(self.request),
                                   MockDBSession))

    def test_login(self):
        d = ponzi_auth.views.login(self.request)
        self.assertEqual(d['status_type'], u'')
        d = ponzi_auth.views.login(self.request, username='foo')
        self.assertEqual(d['status_type'], u'info')

    def test_post_login(self):
        self.request.method = 'POST'
        self.request.params['form.submitted'] = True
        self.request.params['username'] = 'user1'
        self.request.params['password'] = 'user1'

        d = ponzi_auth.views.login(self.request)
        self.assertEqual(d['status_type'], u'error')

        class User(ponzi_auth.tables.AnonymousUser):
            def check_password(self, p):
                return True

        self.db_session.add(User())
        d = ponzi_auth.views.login(self.request)
        self.assertTrue(isinstance(d, HTTPFound))

    def test_signup(self):
        # by default signup is disabled
        self.assertRaises(NotFound, lambda: ponzi_auth.views.signup(self.request))

        self.settings['ponzi_auth.allow_signup'] = True
        d = ponzi_auth.views.signup(self.request)
        self.assertEqual(d['status_type'], u'')

    def test_post_signup(self):
        self.settings['ponzi_auth.allow_signup'] = True
        self.request.method = 'POST'
        self.request.params['form.submitted'] = True
        self.request.params['username'] = 'user1'
        self.request.params['password'] = 'user1'
        self.request.params['firstname'] = 'foo'

        # should successfully sign up and add a new user
        d = ponzi_auth.views.signup(self.request)
        self.assertEqual(d['status_type'], u'info')

        # will fail because of creating with same username
        d = ponzi_auth.views.signup(self.request)
        self.assertEqual(d['status_type'], u'error')

    def test_logout(self):
        d = ponzi_auth.views.logout(self.request)
        self.assertTrue(isinstance(d, HTTPFound))

    def test_find_user(self):
        d = ponzi_auth.views.find_user(self.request)
        self.assertTrue(d is None)
        self.assertRaises(NoResultFound,
                          lambda: ponzi_auth.views.find_user(self.request, username='foo'))

    def test_find_groups(self):
        user = ponzi_auth.tables.AnonymousUser()
        find_groups = ponzi_auth.views.find_groups
        self.assertEqual([], [x for x in find_groups(None, self.request)])
        self.assertEqual([], [x for x in find_groups(user, self.request)])
        self.assertRaises(NoResultFound,
                          lambda: self.assertEqual([], [x for x in find_groups('foo', self.request)]))
