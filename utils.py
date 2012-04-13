""" wrapid: Web Resource API server framework built on Python WSGI.

Various utility functions.
"""

import time
import urllib
import unicodedata


HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD']

DATE_ISO_FORMAT = '%Y-%m-%d'
TIME_ISO_FORMAT = '%H:%M:%S'
DATETIME_ISO_FORMAT = "%sT%sZ" % (DATE_ISO_FORMAT, TIME_ISO_FORMAT)
DATETIME_WEB_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'


def now(format=DATETIME_ISO_FORMAT):
    "Current date and time (UTC) in ISO format."
    return time.strftime(format, time.gmtime())

def now_date(format=DATE_ISO_FORMAT):
    "Current date (UTC) in ISO format."
    return now(format=format)

def now_time(format=TIME_ISO_FORMAT):
    "Current time (UTC) in ISO format."
    return now(format=format)

def rstr(value):
    "Return str of unicode value, else same, recursively."
    if value is None:
        return None
    elif isinstance(value, unicode):
        return str(value)
    elif isinstance(value, list):
        return map(rstr, value)
    elif isinstance(value, tuple):
        return tuple(map(rstr, value))
    elif isinstance(value, set):
        return set(map(rstr, value))
    elif isinstance(value, dict):
        return dict([(rstr(key), rstr(value))
                     for key, value in value.iteritems()])
    else:
        return value

def to_bool(value):
    """Convert the string value to boolean.
    Raise ValueError if not interpretable.
    """
    if not value: return False
    value = value.lower()
    if value in ('true', 't', 'on', 'yes', '1'):
        return True
    elif value in ('false', 'f', 'off', 'no', '0'):
        return False
    else:
        raise ValueError("invalid literal '%s' for boolean" % value)

def to_ascii(value):
    "Convert any non-ASCII character to its closest equivalent."
    value = unicode(value)
    return unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')

def url_build(*segments, **query):
    "Build a URL from the segments and the query."
    url = '/'.join(map(str, segments))
    if query:
        items = dict([(k,v) for k,v in query.iteritems() if v is not None])
        return url + '?' + urllib.urlencode(items)
    else:
        return url


if __name__ == '__main__':
    print now()
    print now_date()
    print now_time()
