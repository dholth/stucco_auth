"""
SQLAlchemy-backed user/group implementation.

Schema inspired by django.contrib.auth
"""

import datetime

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Unicode, Integer, Boolean
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import relationship

from cryptacular.core import DelegatingPasswordManager
from cryptacular.bcrypt import BCRYPTPasswordManager

from ponzi_auth import base
Base = declarative_base()

SCHEMA_VERSION = 0

users_groups = sqlalchemy.Table('user_group', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.user_id'), 
        primary_key=True, nullable=False),
    Column('group_id', Integer, ForeignKey('group.group_id'), 
        primary_key=True, nullable=False), 
    )

class Group(Base):
    __tablename__ = 'group'
    group_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(30), unique=True, nullable=False)

    def __str__(self):
        return 'group:%s' % self.name

base.AbstractGroup.register(Group)


class User(Base):
    __tablename__ = 'user'

    # When fallbacks are set, DelegatingPasswordManager will recognize
    # and automatically upgrade those password formats to the preferred
    # format when the correct password is provided:
    passwordmanager = DelegatingPasswordManager(
            preferred=BCRYPTPasswordManager(),
            fallbacks=()
            )

    user_id = Column(Integer, primary_key=True, nullable=False)
    username = Column(Unicode(30), unique=True, nullable=False, index=True)
    first_name = Column(Unicode(30))
    last_name = Column(Unicode(30))
    email = Column(Unicode(30))
    password = Column(String(80), default='', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime)
    last_password_change = Column(DateTime, default=datetime.date(2001,1,1))
    date_joined = Column(DateTime, default=sqlalchemy.func.current_timestamp())

    groups = relationship(Group,
            secondary = users_groups,
            backref="users")

    def __init__(self, **kwargs):
        for key,value in kwargs.items():
            if key == 'password':
                self.set_password(value)
            else:
                setattr(self, key, value)

    def is_anonymous(self):
        return False

    def set_password(self, raw_password):
        self.password = self.passwordmanager.encode(raw_password)
        self.last_password_change = sqlalchemy.func.current_timestamp()

    def check_password(self, raw_password):
        if not self.is_active: return False
        return self.passwordmanager.check(self.password, raw_password,
                setter=self.set_password)

    def __str__(self):
        return 'user:%s' % self.username

base.AbstractUser.register(User)

class AnonymousUser(User):

    username = u'anonymous'
    email = u""
    first_name = u'(not logged in)'
    last_name = u''
    is_active = False
    user_id = -1
    groups = ()

    def is_anonymous(self):
        return True

    def check_password(self, raw_password):
        return False

class PasswordReset(Base):
    """A password reset token. Good for one password reset."""

    __tablename__ = 'password_reset'
    
    # for example, uuid.uuid4():
    code = Column(Unicode(36), nullable=False, primary_key=True)
    expires = Column(DateTime, default=None, nullable=True)
    created = Column(DateTime, default=sqlalchemy.func.current_timestamp(), nullable=False)
    user_id = Column(Integer, ForeignKey(User.user_id), nullable=False, index=True)
    user = relationship(User)

    def isexpired(self):
        return self.expires is None or self.expires < datetime.datetime.utcnow()

def initialize(session):
    import ponzi_evolution
    # XXX call this every time?
    ponzi_evolution.initialize(session)
    from ponzi_evolution import SQLAlchemyEvolutionManager
    Base.metadata.create_all(session.bind)
    manager = SQLAlchemyEvolutionManager(session, 'ponzi_auth.evolve',
            SCHEMA_VERSION,
            packagename='ponzi_auth')
    if manager.get_db_version() is None:
        manager.set_db_version(SCHEMA_VERSION)
