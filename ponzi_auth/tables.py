"""
SQLAlchemy-backed user/group implementation.

Schema inspired by django.contrib.auth
"""

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Unicode, Integer, Boolean
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import relationship

from cryptacular.core import DelegatingPasswordManager
from cryptacular.bcrypt import BCRYPTPasswordManager

Base = declarative_base()

users_groups = sqlalchemy.Table('user_group', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.user_id'), 
        primary_key=True, nullable=False),
    Column('group_id', Integer, ForeignKey('group.group_id'), 
        primary_key=True, nullable=False), 
    )

class Group(Base):
    __tablename__ = 'group'

    group_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(30))

    def __str__(self):
        return 'group:%s' % self.name

class User(Base):
    __tablename__ = 'user'

    # When fallbacks are set, DelegatingPasswordManager will recognize
    # and automatically upgrade those password formats to the preferred
    # format when the correct password is provided:
    passwordmanager = DelegatingPasswordManager(preferred=BCRYPTPasswordManager(),
            fallbacks=())

    user_id = Column(Integer, primary_key=True, nullable=False)
    username = Column(Unicode(30), unique=True, nullable=False)
    first_name = Column(Unicode(30))
    last_name = Column(Unicode(30))
    email = Column(Unicode(30))
    password = Column(String(80), default='', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime)
    last_password_change = Column(DateTime, default=None)
    date_joined = Column(DateTime, default=sqlalchemy.func.current_timestamp())    

    groups = relationship(Group,
            secondary = users_groups,
            backref="users")

    def is_anonymous(self):
        return False

    def set_password(self, raw_password):
        self.password = self.passwordmanager.encode(raw_password)

    def check_password(self, raw_password):
        if not self.is_active: return False
        return self.passwordmanager.check(self.password, raw_password,
                setter=self.set_password)

    def __str__(self):
        return 'user:%s' % self.username

class AnonymousUser(User):

    def __init__(self):
        self.user_id = 0
        self.username = 'anonymous'
        
    def is_anonymous(self):
        return True

    def check_password(self, raw_password):
        return False

def initialize(session):
    Base.metadata.create_all(session.bind)
