""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Login to an account other than 'anonymous'. Uses Basic Authentication.
"""

import logging

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
            logging.debug('wrapid: anonymous login is not good enough')
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=realm)
        try:
            self.location = request.get_value('href')
            if not self.location: raise KeyError
        except KeyError:
            self.location = application.url
        # The cookie remedies an apparent deficiency of several
        # human browsers: For some pages in the site (notably
        # the application root '/'), the authentication data does not
        # seem to be sent voluntarily by the browser.
        self.cookie = "%s-login=yes; Path=%s" % (realm, application.path)

    def get_response(resource, request, application):
        logging.debug("wrapid: login redirect to %s", url)
        return HTTP_SEE_OTHER(Location=self.location, Set_Cookie=self.cookie)
