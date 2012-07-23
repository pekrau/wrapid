""" wrapid: Micro framework built on Python WSGI for RESTful server APIs

HTTP response classes.
"""

import sys
import httplib
import wsgiref.headers


class Response(Exception):
    "Base class for HTTP responses."

    http_code = None

    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args)
        self.headers = wsgiref.headers.Headers([(k.replace('_', '-'), v)
                                                for (k,v) in kwargs.items()
                                                if v is not None])
        self.content = list(args)

    def __str__(self):
        return "%s %s" % (self.http_code, httplib.responses[self.http_code])

    def __setitem__(self, key, value):
        self.headers[key] = value

    def __call__(self, start_response):
        start_response(str(self), self.headers.items())
        return self

    def __iter__(self):
        return iter(map(str, self.content))

    def append(self, data):
        self.content.append(data)


class HTTP_SUCCESS(Response): pass

class HTTP_OK(HTTP_SUCCESS):
    http_code = httplib.OK

class HTTP_CREATED(HTTP_SUCCESS):
    http_code = httplib.CREATED

class HTTP_ACCEPTED(HTTP_SUCCESS):
    http_code = httplib.ACCEPTED

class HTTP_NO_CONTENT(HTTP_SUCCESS):
    http_code = httplib.NO_CONTENT


class HTTP_REDIRECTION(Response): pass

class HTTP_MOVED_PERMANENTLY(HTTP_REDIRECTION):
    http_code = httplib.MOVED_PERMANENTLY

class HTTP_FOUND(HTTP_REDIRECTION):
    http_code = httplib.FOUND

class HTTP_SEE_OTHER(HTTP_REDIRECTION):
    http_code = httplib.SEE_OTHER

class HTTP_NOT_MODIFIED(HTTP_REDIRECTION):
    http_code = httplib.NOT_MODIFIED

class HTTP_TEMPORARY_REDIRECT(HTTP_REDIRECTION):
    http_code = httplib.TEMPORARY_REDIRECT


class HTTP_ERROR(Response):

    def __call__(self, start_response):
        start_response(str(self), self.headers.items(), sys.exc_info())
        return self


class HTTP_CLIENT_ERROR(HTTP_ERROR): pass

class HTTP_BAD_REQUEST(HTTP_CLIENT_ERROR):
    http_code = httplib.BAD_REQUEST

class HTTP_UNAUTHORIZED(HTTP_CLIENT_ERROR):
    http_code = httplib.UNAUTHORIZED

class HTTP_UNAUTHORIZED_BASIC_CHALLENGE(HTTP_UNAUTHORIZED):
    def __init__(self, *args, **kwargs):
        realm = kwargs.pop('realm', 'unspecified')
        super(HTTP_UNAUTHORIZED_BASIC_CHALLENGE, self).__init__(*args, **kwargs)
        self.headers['www-authenticate'] = 'Basic realm="%s"' % realm

class HTTP_FORBIDDEN(HTTP_CLIENT_ERROR):
    http_code = httplib.FORBIDDEN

class HTTP_NOT_FOUND(HTTP_CLIENT_ERROR):
    http_code = httplib.NOT_FOUND

class HTTP_METHOD_NOT_ALLOWED(HTTP_CLIENT_ERROR):
    http_code = httplib.METHOD_NOT_ALLOWED

class HTTP_NOT_ACCEPTABLE(HTTP_CLIENT_ERROR):
    http_code = httplib.NOT_ACCEPTABLE

class HTTP_REQUEST_TIMEOUT(HTTP_CLIENT_ERROR):
    http_code = httplib.REQUEST_TIMEOUT

class HTTP_CONFLICT(HTTP_CLIENT_ERROR):
    http_code = httplib.CONFLICT

class HTTP_GONE(HTTP_CLIENT_ERROR):
    http_code = httplib.GONE


class HTTP_SERVER_ERROR(HTTP_ERROR): pass

class HTTP_INTERNAL_SERVER_ERROR(HTTP_SERVER_ERROR):
    http_code = httplib.INTERNAL_SERVER_ERROR

class HTTP_NOT_IMPLEMENTED(HTTP_SERVER_ERROR):
    http_code = httplib.NOT_IMPLEMENTED

class HTTP_SERVICE_UNAVAILABLE(HTTP_SERVER_ERROR):
    http_code = httplib.SERVICE_UNAVAILABLE
