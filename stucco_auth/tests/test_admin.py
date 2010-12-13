"""
Tests for admin.py
"""

from nose.tools import raises

import validatish

from stucco_auth import admin
from stucco_auth import tables

def test_is_admin():
    u = tables.User()
    assert not admin.is_admin(u)
    u.groups.append(tables.Group(name='admin'))
    assert admin.is_admin(u)
    
def test_get_user():
    USER = "A Nice User"
    class MockSession(object):
        def query(self, cls_):    
            return self
        def get(self, key):
            return USER
    
    class MockRequest(object):
        pass
    
    r = MockRequest()
    r.db = MockSession()
    assert admin.get_user(r) == USER
    
def test_strong_password():
    @raises(validatish.Invalid)
    def invalid():
        admin.StrongPassword('two')
    invalid()
    admin.StrongPassword('foobar')
    
def test_optional_strong_password():
    admin.OptionalStrongPassword(None)
    admin.OptionalStrongPassword('password')
    
def test_required_strong_password():
    @raises(validatish.Invalid)
    def invalid():
        admin.RequiredStrongPassword(None)
    invalid()
    admin.RequiredStrongPassword('password')

def test_username_rules():
    @raises(validatish.Invalid)
    def invalid():
        admin.Username('#')    
    invalid()
    admin.Username('foo_bar.123@example.org')
    
    