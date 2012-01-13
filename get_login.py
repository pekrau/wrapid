""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Login to an account other than 'anonymous'. Uses Basic Authentication.
"""

import logging

from .resource import *
from .utils import get_account_basic_authentication


class GET_Login(Method):
    "Login to an account other than 'anonymous'. Uses Basic Authentication."

    def __init__(self, realm, get_account):
        "Set the realm and account retrieval and authentication function."
        self.realm = realm
        self.get_account = get_account

    def __call__(self, resource, request, application):
        account = get_account_basic_authentication(request,
                                                   self.realm,
                                                   self.get_account)
        if account['name'] == 'anonymous':
            logging.debug('wrapid: anonymous login is not good enough')
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=self.realm)
        else:
            try:
                url = request.get_value('href')
                if not url: raise KeyError
            except KeyError:
                url = application.url
            # The cookie remedies an apparent deficiency of several
            # human browsers: For some pages in the site (notably
            # the application root '/'), the authentication data does not
            # seem to be sent voluntarily by the browser.
            cookie = "%s-login=yes; Path=%s" % (self.realm, application.path)
            logging.debug("wrapid: login redirect to %s", url)
            raise HTTP_SEE_OTHER(Location=url, Set_Cookie=cookie)
