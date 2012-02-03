""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Login to an account other than 'anonymous'. Uses Basic Authentication.
"""

from .resource import *
from .utils import get_account_basic_authentication


class GET_Login(Method):
    "Login to an account other than 'anonymous'. Uses Basic Authentication."

    def __init__(self, get_account):
        "Set the account retrieval and authentication function."
        self.get_account = get_account

    def handle(self, resource, request, application):
        realm = application.name
        account = get_account_basic_authentication(request,
                                                   realm,
                                                   self.get_account)
        if account['name'] == 'anonymous':
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=realm)
        try:
            self.redirect = request.get_value('href')
            if not self.redirect: raise KeyError
        except KeyError:
            self.redirect = application.url
        # The cookie remedies an apparent deficiency of several
        # human browsers: For some pages in the site (notably
        # the application root '/'), the authentication data does not
        # seem to be sent voluntarily by the browser.
        self.cookie = "%s-login=yes; Path=%s" % (realm, application.path)

    def get_response(self, resource, request, application):
        return HTTP_SEE_OTHER(Location=self.redirect, Set_Cookie=self.cookie)
