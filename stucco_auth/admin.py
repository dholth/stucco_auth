# -*- coding: utf-8 -*-
"""
Views for the administration interface.

The views in this file currently require a SQLAlchemy Session as request.db.
"""

from pyramid_formish import ValidationError
from pyramid.renderers import get_renderer
from pyramid.security import authenticated_userid
from pyramid.url import model_url
from smtplib import SMTPException
from sqlalchemy import and_
from webob.exc import HTTPSeeOther
import datetime
import formish
import schemaish
import sqlalchemy.orm
import uuid
import validatish

from stucco_auth.tables import User, PasswordReset

import logging
log = logging.getLogger(__name__)


# XXX Originally these utility functions were implemented in other modules.
# They should probably be moved:

def set_flash(*args, **kw):
    pass # not implemented

def is_admin(user):
    # XXX implement user.is_admin() instead?
    for group in user.groups:
        if group.name == 'admin':
            return True
    return False

def get_user(request):
    return request.db.query(User).get(authenticated_userid(request))


def StrongPassword(password):
    if len(password) < 5: # XXX a better implementation is in cracklib
        raise validatish.Invalid(u"Password must be at least 5 characters long.")

def OptionalStrongPassword(password):
    """Check password if it is not None"""
    if password != None:
        StrongPassword(password)

def RequiredStrongPassword(password):
    # Not using validatish.All(Required, ...) because it does not shortcut,
    # sending None to StrongPassword when the Required() fails.)
    if isinstance(password, basestring) and password:
        StrongPassword(password)
    else:
        raise validatish.Invalid(u"Required.")

def Username(username):
    """Usernames must be all lowercase and contain only letters, numbers,
    and limited punctuation."""
    validatish.is_plaintext(username, '._@')


import hmac
import hashlib

def reset_code(user):
    """Return a new password reset code for user."""
    reset = PasswordReset()
    reset.code = str(uuid.uuid4())
    reset.expires = datetime.datetime.utcnow() + datetime.timedelta(days=3)
    reset.user = user
    return reset

def generate_csrf_token(object, context, request):
    """Generate a token that is unique per session and form URL, or None
    if the user is not logged in."""
    csrf_secret = request.registry.settings['ponzi_csrf_secret']
    userid = authenticated_userid(request)
    if userid is None:
        return None
    m = hmac.new(csrf_secret,
        ''.join((str(userid),
            str(object.__class__), 
            request.url, 
            request.session.id)),
        hashlib.sha1
        )
    return m.hexdigest()

from functools import wraps

def check_csrf(f):
    @wraps(f)
    def wrapper(self, *args, **kw):
        if self.csrf_token:
            if self.csrf_token != self.request.POST.get('__csrf_token__', None):
                log.warn('Bad or missing csrf token from %s', self.request.remote_addr)
                raise ValidationError(**{'__csrf_token__': 'Bad csrf token'})
        return f(self, *args, **kw)
    return wrapper

class CSRFForm(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def csrf_token(self):
        try:
            return self._csrf_token
        except AttributeError:
            self._csrf_token = generate_csrf_token(self, self.context, self.request)
            return self._csrf_token

class ForgotPasswordFormController(object):
    """Allow users to send themselves password reset codes."""
    relay = None # lamson mail relay

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        rc = {'title':u'Lost Password'}
        return rc

    def form_fields(self):
        fields = [('username', schemaish.String())]
        return fields

    def handle_submit(self, data):
        flash = u'Thank you. You should receive a password reset link in your e-mail.'
        username = data['username']
        try:
            user = self.request.db.query(User) \
                .filter_by(username=username).one()

            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            requests = self.request.db.query(PasswordReset)\
                    .filter(and_(PasswordReset.user == user, 
                            PasswordReset.created > cutoff,
                            PasswordReset.expires != None))\
                                    .count()
            
            if not user.is_active:
                flash = u'That account is inactive. Password cannot be reset.'
                log.info(u"Password request for inactive account %s %s from %s", 
                        user.user_id, user.username, self.request.remote_addr)
            elif requests < 3:
                reset = reset_code(user)
                template = get_renderer('passwordreset.txt')
                body = template.template.render(dict(request=self.request, data=data, reset=reset))
                self.relay.send(To=user.email, From=u'noreply',
                        Subject=u'Password Reset', Body=body)
                log.info(u"Sent password reset code to %s %s from %s", 
                        user.user_id, user.username, self.request.remote_addr)
            else:
                flash = u'Too many requests. You may only request 3 password reset codes per day.'
                log.info(u"Excessive password reset requests for %s %s from %s", 
                        user.user_id, user.username, self.request.remote_addr)

        except sqlalchemy.orm.exc.NoResultFound:
            flash = 'Username not found.'

        set_flash(self.request, flash)
        return {}

    def success(self):
        return {}


class PasswordResetFormController(object):
    """Allow users with valid, non-expired password reset codes to set a new password."""
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        new_code = model_url(self.context.__parent__, self.request)
        rc = {'expired':self.context.token.isexpired(), 'new_code':new_code}
        return rc

    def form_defaults(self):
        user = self.context.token.user
        return {'username':user.username, 
                'first_name': user.first_name, 
                'last_name': user.last_name, 
                'email': user.email }

    def form_fields(self):
        fields = [
                ('username', schemaish.String(description=u"Used to log in.")),
                ('first_name', schemaish.String()),
                ('last_name', schemaish.String()),
                ('email', schemaish.String()),
                ('password', schemaish.String(validator=RequiredStrongPassword))
                ]
        return fields

    def form_widgets(self, form_fields):
        widgets = {}
        for items in form_fields:
            name = items[0]
            widgets[name] = formish.Input(readonly=True)
        widgets['password'] = formish.CheckedPassword()
        return widgets

    def handle_submit(self, data):
        if self.context.token.isexpired():
            raise HTTPSeeOther(location=model_url(self.context))
        self.context.user.set_password(data['password'])
        pwreset_table = sqlalchemy.orm.util.class_mapper(PasswordReset).tables[0]
        self.request.db.execute(pwreset_table.update()\
                .where(pwreset_table.c.user_id==self.context.user.user_id)\
                .values(expires=None))
        raise HTTPSeeOther(location=model_url(self.context.__parent__, self.request, 'success'))


class EditUserFormController(CSRFForm):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        rc = {'title':u'Edit User'}
        return rc

    def form_fields(self):
        admin = is_admin(get_user(self.request))

        fields = [ ('username', schemaish.String(description=u"Used to log in.")), ]

        if admin:
            fields.append(('is_active',
                schemaish.Boolean(description=u"May log in?")))

        fields.extend([
                ('email', schemaish.String()),
                ('first_name', schemaish.String()),
                ('last_name', schemaish.String()),
                ])

        if not admin:
            fields.extend([
                ('current_password', schemaish.String(
                    description=u"Required if changing password."))
                ])

        fields.extend([
                ('password', schemaish.String(validator=OptionalStrongPassword,
                    description="New password."))
                ])

        return fields

    def form_defaults(self):
        return dict(username=self.context.username,
                email=self.context.email,
                first_name=self.context.first_name,
                last_name=self.context.last_name,
                is_active=self.context.is_active,)

    def form_widgets(self, fields):
        return {'username':formish.Input(readonly=True),
                'current_password':formish.Password(),
                'password':formish.CheckedPassword(),
                'is_active':formish.Checkbox(),}

    @check_csrf
    def handle_submit(self, data):
        admin = is_admin(get_user(self.request))
        # XXX some of this checking may be redundant with Formish's
        # readonly=True enforcement:
        for key in data:
            if key in ('email', 'first_name', 'last_name'):
                setattr(self.context, key, data[key])
            elif key == 'is_active' and admin:
                # don't let non-admins deactivate themselves.
                setattr(self.context, key, data[key])
            elif key == 'password' and data[key]:
                if not admin:
                    u = get_user(self.request)
                    if not isinstance(data['current_password'], basestring) \
                            or not u.check_password(data['current_password']):
                        ve = ValidationError()
                        ve.errors = {'current_password':
                            u'Correct current password is required to set new password.'}
                        raise ve

                self.context.set_password(data[key])

        location = model_url(self.context, self.request)
        set_flash(self.request, u"User edited.")
        return HTTPSeeOther(location=location)


class CreateUserFormController(EditUserFormController):
    relay = None # set to a Lamson e-mail relay

    def __call__(self):
        rc = {'title':u'Create User'}
        return rc

    def form_fields(self):
        fields = EditUserFormController.form_fields(self)
        fields.append(
                ('send_email',
                    schemaish.Boolean(
                        description=u"Send a password reset e-mail instead " 
                        u"of setting an initial password.")))
        return fields

    def form_widgets(self, fields):
        widgets = EditUserFormController.form_widgets(self, fields)
        widgets.update({
            'username':formish.Input(),
            'send_email':formish.Checkbox(),
            'is_active':formish.Hidden(),
            })
        return widgets

    def form_defaults(self):
        return {'send_email':True}

    @check_csrf
    def handle_create(self, data):
        attributes = ['username', 'first_name', 'last_name', 'email']
        data['username'] = data['username'].lower()
        kwargs = dict((k, data[k]) for k in attributes)
        user = User(is_active=True, **kwargs)
        user.date_joined = sqlalchemy.func.current_timestamp()

        if data['password']:
            user.set_password(data['password'])

        try:
            Username(user.username)
        except validatish.Invalid, e:
            ve = ValidationError()
            ve.errors = {'username': e.message}
            raise ve
        
        if self.request.db.query(User).filter(User.username==user.username).count():
            ve = ValidationError()
            ve.errors = {'username': u'This username is taken.'}
            raise ve

        if data['send_email']:
            reset = reset_code(user)
            template = get_renderer('new_user.txt')
            body = template.template.render(dict(request=self.request, data=data, reset=reset))
            try:
                self.relay.send(To=user.email, From=u'noreply',
                        Subject=u'Account Created', Body=body)
                log.info(u"Sent password reset code to %s %s from %s", 
                        user.user_id, user.username, self.request.remote_addr)
            except SMTPException, e:
                ve = ValidationError()
                ve.errors = {'email':'Could not send to this address.'}
                raise ve

        self.request.db.add(user)

        # add user to at least one group?
        
        set_flash(self.request, u'User created.')

        new_user_location = model_url(self.context, self.request,
                str(user.user_id))

        return HTTPSeeOther(location=new_user_location)

