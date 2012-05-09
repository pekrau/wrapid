""" wrapid: Web Resource API server framework built on Python WSGI.

Various utility functions.
"""

import time
import urllib
import urlparse
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
    "Return unicode value encoded using UTF-8, else same, recursively."
    if isinstance(value, unicode):
        return value.encode('utf-8', 'ignore')
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

def runicode(value):
    """Return string value decoded into unicode, else same, recursively.
    Assumes strings use UTF-8 encoding."""
    if isinstance(value, basestring):
        if isinstance(value, unicode):
            return value
        else:
            return unicode(value, 'utf-8')
    elif isinstance(value, list):
        return map(runicode, value)
    elif isinstance(value, tuple):
        return tuple(map(runicode, value))
    elif isinstance(value, set):
        return set(map(runicode, value))
    elif isinstance(value, dict):
        return dict([(runicode(k), runicode(v)) for k, v in value.iteritems()])
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
    base = segments[0]
    tail = segments[1:]
    if tail:
        base = base.rstrip('/') + '/'
        url = urlparse.urljoin(base, '/'.join(map(str, tail))).rstrip('/')
    else:
        url = base
    if query:
        items = dict([(k,v) for k,v in query.iteritems() if v is not None])
        return url + '?' + urllib.urlencode(items)
    else:
        return url


if __name__ == '__main__':
    print now()
    print now_date()
    print now_time()
