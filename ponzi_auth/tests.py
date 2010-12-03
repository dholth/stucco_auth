import unittest

from pyramid.configuration import Configurator
from pyramid import testing

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = Configurator()
        self.config.begin()

    def tearDown(self):
        self.config.end()

    def test_my_view(self):
        from ponzi_auth.views import my_view
        request = testing.DummyRequest()
        info = my_view(request)
        self.assertEqual(info['project'], 'ponzi_auth')

import ponzi_auth.tables
from ponzi_auth.tables import User, Group
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
        user = ponzi_auth.tables.User(is_active=True)
        user.set_password('mimsy')
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


import ponzi_auth

class MainTests(unittest.TestCase):

    def test_main(self):
        app = ponzi_auth.main({})
        assert hasattr(app, 'registry')

import ponzi_auth.models

class ModelsTest(unittest.TestCase):
    
    def test_get_root(self):
        root = ponzi_auth.models.get_root(None)
        assert root is ponzi_auth.models.root
