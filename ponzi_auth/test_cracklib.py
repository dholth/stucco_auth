# -*- coding: utf-8 -*-

from ponzi_auth.cracklib import fascist_check

from nose.tools import raises

@raises(TypeError)
def test_null():
    fascist_check(None)

@raises(TypeError)
def test_notstring():
    fascist_check(45)

@raises(TypeError)
def test_notstring_2():
    fascist_check("", 90)

def test_normal():
    assert len(fascist_check("password"))
    fascist_check(u"京阪式")

