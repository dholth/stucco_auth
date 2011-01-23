"""
SQLAlchemy-backed user/group implementation.

Schema inspired by django.contrib.auth
"""

import datetime
import sqlalchemy
import json

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Unicode, Integer, Boolean, PickleType
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import relationship

from cryptacular.core import DelegatingPasswordManager
from cryptacular.bcrypt import BCRYPTPasswordManager
from stucco_auth.util import PlaceholderPasswordChecker

import logging
log = logging.getLogger(__name__)

Base = declarative_base()

users_groups = sqlalchemy.Table('stucco_user_group', Base.metadata,
    Column('user_id', Integer, ForeignKey('stucco_user.user_id'),
        primary_key=True, nullable=False),
    Column('group_id', Integer, ForeignKey('stucco_group.group_id'),
        primary_key=True, nullable=False),
    )


class Group(Base):
    __tablename__ = 'stucco_group'
    group_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(30), unique=True, nullable=False)

    def __str__(self):
        return 'group:%s' % self.name


class User(Base):
    __tablename__ = 'stucco_user'

    # When fallbacks are set, DelegatingPasswordManager will recognize
    # and automatically upgrade those password formats to the preferred
    # format when the correct password is provided:
    passwordmanager = DelegatingPasswordManager(
            preferred=BCRYPTPasswordManager(),
            fallbacks=(PlaceholderPasswordChecker(),)
            )

    user_id = Column(Integer, primary_key=True, nullable=False)
    username = Column(Unicode(30), unique=True, nullable=False, index=True)
    first_name = Column(Unicode(30))
    last_name = Column(Unicode(30))
    email = Column(Unicode(30))
    password = Column(String(80), default='*', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime)
    last_password_change = Column(DateTime,
                                  default=datetime.date(2001, 1, 1))
    date_joined = Column(DateTime, default=sqlalchemy.func.current_timestamp())

    groups = relationship(Group,
            secondary=users_groups,
            backref="users")

    @property
    def is_anonymous(self):
        return False

    def set_password(self, raw_password):
        self.password = self.passwordmanager.encode(raw_password)
        self.last_password_change = sqlalchemy.func.current_timestamp()

    def check_password(self, raw_password):
        if not self.is_active:
            return False
        return self.passwordmanager.check(self.password, raw_password,
                                          setter=self.set_password)

    def __str__(self):
        # XXX self.user_id is None for new users
        return 'user:%s' % self.user_id


class AnonymousUser(User):
    username = u'anonymous'
    email = u""
    first_name = u'(not logged in)'
    last_name = u''
    is_active = False
    user_id = 0
    groups = []

    @property
    def is_anonymous(self):
        return True

    def check_password(self, raw_password):
        return False


class Settings(Base):
    """Simple key/value settings storage. Value is stored as JSON."""
    __tablename__ = 'stucco_settings'

    key = Column(String(32), nullable=False, primary_key=True)
    value = Column(PickleType(pickler=json))
