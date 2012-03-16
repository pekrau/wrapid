""" wrapid: Web Resource API server framework built on Python WSGI.

Login mixin and challenge method. Basic Authentication.
"""

import base64
import hashlib

from .resource import *


def decode_authorization_header(request):
    """Return the account name and password from the request header.
    Raise ValueError if not present or malformed.
    """
    value = request.headers['Authorization']
    if not value: raise ValueError
    parts = value.split()
    if parts[0].lower() != 'basic': raise ValueError
    if len(parts) != 2: raise ValueError
    return base64.standard_b64decode(parts[1]).split(":", 1)


class LoginMixin(object):
    "Mixin class for setting login in a method. Basic Authentication."

    def set_login(self, resource, request, application):
        """Set the attribute 'login' account dictionary from
        the Basic Authentication in the request.
        Raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE if no account specified,
        and anonymous login is disallowed.
        Raise HTTP_FORBIDDEN if no such account or wrong password.
        """
        try:
            name, password = decode_authorization_header(request)
        except ValueError:
            # The cookie remedies an apparent deficiency of several
            # human browsers: For some pages in the site (notably
            # the application root '/'), the authentication data
            # does not seem to be sent voluntarily by the browser.
            if request.cookie.has_key("%s-login" % application.name):
                raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=application.name)
            else:
                try:
                    self.login = self.get_account_anonymous()
                except KeyError:
                    raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=application.name)
        else:
            try:
                self.login = self.get_account(name, password)
            except (KeyError, ValueError):
                raise HTTP_FORBIDDEN('invalid account or password')

    def get_account(self, name, password=None):
        """Return a dictionary describing the account:
        name, description, email, teams and properties.
        If password is provided, authenticate the account.
        Raise KeyError if there is no such account.
        Raise ValueError if the password does not match.
        """
        raise NotImplementedError

    def get_account_anonymous(self):
        """Return the dictionary describing the anonymous account.
        Raise KeyError if disallowed.
        """
        raise KeyError


class GET_Login(Method):
    "Perform login to an account. Basic Authentication."

    def __init__(self, get_account, max_age=18*60*60):
        "Set the account retrieval and authentication function."
        self.get_account = get_account
        self.max_age = max_age

    def handle(self, resource, request, application):
        try:
            name, password = decode_authorization_header(request)
            account = self.get_account(name, password)
        except (KeyError, ValueError):
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=application.name)
        try:
            self.redirect = request.get_value('href')
            if not self.redirect: raise KeyError
        except KeyError:
            self.redirect = application.url
        # The cookie remedies an apparent deficiency of several
        # human browsers: For some pages in the site (notably
        # the application root '/'), the authentication data
        # does not seem to be sent voluntarily by the browser.
        
        self.cookie = "%s-login=yes; path=%s" % (application.name,
                                                 application.path)
        if self.max_age:
            self.cookie += "; max-age=%s" % self.max_age

    def get_response(self, resource, request, application):
        return HTTP_SEE_OTHER(Location=self.redirect, Set_Cookie=self.cookie)