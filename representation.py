""" wrapid: Web Resource API server framework built on Python WSGI.

Abstract representation class.
"""

import wsgiref.headers

from .responses import *


class Representation(object):
    "Output representation generator for a specified mimetype."

    mimetype = None
    format = None
    cache_control = 'max-age=3600'

    def __init__(self, descr=None):
        self._descr = descr
        self.headers = wsgiref.headers.Headers([('Content-Type',self.mimetype)])

    def get_http_headers(self):
        """Get the dictionary of HTTP headers,
        suitable when creating an HTTP_OK instance.
        """
        return dict(self.headers)

    def set_cache_control_headers(self, cacheable):
        "Set the HTTP headers for cache control."
        if cacheable is None:
            return
        elif cacheable:
            self.headers.add_header('Cache-Control', self.cache_control)
        else:
            self.headers.add_header('Cache-Control', 'no-cache')
            self.headers.add_header('Pragma', 'no-cache')
            self.headers.add_header('Expires', '-1')

    @property
    def descr(self):
        if self._descr:
            return self._descr
        else:
            return self.__doc__

    def __call__(self, data):
        "Return the response instance containing the representation."
        raise NotImplementedError
