""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Various utility functions.
"""

import base64

from .response import HTTP_UNAUTHORIZED_BASIC_CHALLENGE


HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE']


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
    The function 'get_account' takes an account name and returns
    the account dictionary **without any authentication**.
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
            try:
                result = get_account(name)
            except KeyError:
                raise
            else:
                variables['account'] += variables['FORMAT']
                variables['FORMAT'] = None
        else:
            raise
    return result

def get_account_basic_authentication(request, realm, get_account):
    """Return the account dictionary given basic authentication data
    in the request. If none (and none available according to the cookie),
    then return the account 'anonymous'.
    Raise KeyError if no account found.
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
        return get_account('anonymous')
    else:
        try:
            return get_account(name, password)
        except (KeyError, ValueError):
            return get_account('anonymous')
