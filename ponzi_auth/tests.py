import unittest

from pyramid.configuration import Configurator
# from pyramid import testing

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = Configurator()
        self.config.begin()

    def tearDown(self):
        self.config.end()

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

    def test_passwordreset(self):
        pass

import ponzi_auth

class MainTests(unittest.TestCase):

    def test_main(self):
        app = ponzi_auth.main({})
        assert hasattr(app, 'registry')

from ponzi_auth.models import Locatable, KeyTraverser, get_root

class ModelsTest(unittest.TestCase):
    
    def test_get_root(self):
        root = get_root(None)
        assert root is not None

    def test_mixins(self):
        class FooBar(KeyTraverser, Locatable):
            def __init__(self, name=None, parent=None, session=None):
                KeyTraverser.__init__(self, session=session)
                Locatable.__init__(self, name=name, parent=parent)
        
        class BarFoo(Locatable, KeyTraverser):
            def __init__(self, name=None, parent=None, session=None):
                Locatable.__init__(self, name=name, parent=parent)
                KeyTraverser.__init__(self, session=session)

        fb = FooBar(name='foobar', parent='parent', session='a session')
        assert fb.__name__ == 'foobar', fb.__name__
        assert fb.__parent__ == 'parent'
        assert fb.session == 'a session'

        bf = BarFoo(name='barfoo', parent='parent', session='a session')
        assert bf.__name__ == 'barfoo'
        assert bf.__parent__ == 'parent'
        assert bf.session == 'a session'

