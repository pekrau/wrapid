"""wrapid: Web Resource Application Programming Interface built on Python WSGI.

Various general utility functions.
"""

import base64

from .response import HTTP_UNAUTHORIZED_BASIC_CHALLENGE


def basic_authentication(request, realm):
    """Return the user and password provided in the request.
    Raise the appropriate HTTP status if not provided.
    """
    try:
        value = request.headers['Authorization']
        if not value: raise ValueError
        parts = value.split()
        if parts[0].lower() != 'basic': raise ValueError
        if len(parts) != 2: raise ValueError
    except ValueError:
        raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm=realm)
    return base64.standard_b64decode(parts[1]).split(":", 1)
