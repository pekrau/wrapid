""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Various utility functions.
"""

import base64
import time
import hashlib

from .response import HTTP_UNAUTHORIZED_BASIC_CHALLENGE


HTTP_METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS']

DATETIME_ISO_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DATETIME_WEB_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'


def now(format=DATETIME_ISO_FORMAT):
    return time.strftime(format, time.gmtime())

def basic_authentication(request, realm, require=True):
    """Return the user and password provided in the request.
    Raise the appropriate HTTP status if not provided and 'require' is True,
    else just raise ValueError.
    """
    try:
        value = request.headers['Authorization']
        if not value: raise ValueError
        parts = value.split()
        if parts[0].lower() != 'basic': raise ValueError
        if len(parts) != 2: raise ValueError
    except ValueError:
        if require:
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=realm)
        else:
            raise
    return base64.standard_b64decode(parts[1]).split(":", 1)

def identify_account(variables, get_account):
    """Return the account dictionary given the 'variables' lookup,
    which is assumed to contain an item 'account'.
    The 'get_account' argument is a function which takes an account name
    and returns the account dictionary **without any authentication**.
    It must raise KeyError if there is no such account.
    This handles the case where an account name containing a dot and
    a short (<=4 chars) last name, which will otherwise be confused
    for a FORMAT specification.
    Raise KeyError if no account found.
    """
    try:
        result = get_account(variables['account'])
    except KeyError:
        if variables.get('FORMAT'):
            name = variables['account'] + variables['FORMAT']
            result = get_account(name)
            variables['account'] += variables['FORMAT']
            variables['FORMAT'] = None
        else:
            raise
    return result

def get_account_basic_authentication(request, realm, get_account):
    """Return the account dictionary given basic authentication data
    in the request. The argument 'get_account' is a function that takes
    an account name and optionally a password, and returns a dictionary
    describing the account.
    If none (and none available according to the cookie), then return
    the account 'anonymous'.
    Raise KeyError if no such account.
    Raise ValueError if incorrect password.
    """
    try:
        name, password = basic_authentication(request, realm, require=False)
    except ValueError:              # No authentication data
        # The cookie remedies an apparent deficiency of several
        # human browsers: For some pages in the site (notably
        # the application root '/'), the authentication data does not
        # seem to be sent voluntarily by the browser.
        if request.cookie.has_key("%s-login" % realm):
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=realm)
        else:
            return get_account('anonymous')
    else:
        return get_account(name, password)

def get_password_hexdigest(password, salt=''):
    "Return the MD5 hex digest of the password combined with the salt."
    md5 = hashlib.md5()
    md5.update(salt)
    md5.update(password)
    return md5.hexdigest()

def rstr(value):
    "Return str of unicode value, else same, recursively."
    if value is None:
        return None
    elif isinstance(value, unicode):
        return str(value)
    elif isinstance(value, list):
        return map(rstr, value)
    elif isinstance(value, set):
        return set(map(rstr, value))
    elif isinstance(value, dict):
        return dict([(rstr(key), rstr(value))
                     for key, value in value.iteritems()])
    else:
        return value
