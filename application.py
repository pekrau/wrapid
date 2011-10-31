"""wrapid: Web Resource Application Programming Interface built on Python WSGI.

Application class: WSGI interface.
"""

import logging
import traceback
import wsgiref.util
import wsgiref.headers
import cgi
import json
import Cookie

from .response import *
from . import mimeparse


class Application(object):
    """An instance of this class, or a subclass thereof,
    is the Python WSGI interface to a web server.

    The web server must be configured to call an instance of
    this class for all HTTP requests to the relevant URLs.
    """

    def __init__(self, name=None, version=None, debug=False):
        self._name = name
        self.version = version
        self.debug = debug
        self.resources = []

    @property
    def name(self):
        return self._name or self.__class__.__name__

    def __call__(self, environ, start_response):
        "WSGI interface; this method is called for each HTTP request."
        self.url = wsgiref.util.application_uri(environ)
        request = self.get_request(environ)
        logging.debug("wrapid: HTTP method '%s', URL path '%s'",
                      request.http_method,
                      request.urlpath)
        try:
            resource = self.get_resource(request.urlpath)
            if resource is None:
                raise HTTP_NOT_FOUND
            logging.debug("wrapid: %s", resource)
            response = resource(request, self)
            return response(start_response)
        except HTTP_UNAUTHORIZED, error: # Do not log, nor give browser output
            return error(start_response)
        except HTTP_REDIRECTION, error:
            return error(start_response)
        except HTTP_ERROR, error:
            logging.debug("wrapid: HTTP error: %s", error)
            if request.human_user_agent:
                response = HTTP_OK(content_type='text/plain')
                response.append("%s\n\n%s" % (error, ''.join(error.content)))
                return response(start_response)
            else:
                return error(start_response)
        except Exception, message:
            tb = traceback.format_exc(limit=20)
            logging.error("wrapid: exception\n%s", tb)
            error = HTTP_INTERNAL_SERVER_ERROR(content_type='text/plain')
            error.append("%s\n" % error)
            if self.debug:
                error.append('\n')
                error.append(tb)
            return error(start_response)

    def get_request(self, environ):
        "Get the request data in pre-processed form."
        return Request(environ)

    def append(self, resource):
        "Append a resource to the list of available resources."
        self.resources.append(resource)

    def get_resource(self, urlpath):
        """Get the resource that matches the given URL path.
        The list of resources is searched in order for a URL path
        template that matches the request URL path.
        """
        for resource in self.resources:
            if resource.urlpath_template_match(urlpath): return resource

    def get_url(self, *segments, **query):
        """Synthesize an absolute URL from the application URL
        and the given path segments and query.
        """
        url = '/'.join([self.url] + list(segments))
        if query:
            url += '?' + urllib.urlencode(query)
        return str(url)


class Request(object):
    "HTTP request data container."

    # The values must be in lower case.
    HUMAN_USER_AGENT_SIGNATURES = ['mozilla', 'firefox', 'opera',
                                   'chrome', 'safari', 'msie']

    def __init__(self, environ):
        "Standard setup of attributes from the HTTP input data."
        self.environ = environ
        self.urlpath = self.environ['PATH_INFO']
        self.http_method = self.environ['REQUEST_METHOD']
        self.human_user_agent = self.is_human_user_agent()
        # Obtain the HTTP headers for the request.
        self.headers = wsgiref.headers.Headers([])
        for key in self.environ:
            if key.startswith('HTTP_'):
                self.headers[key[5:]] = str(self.environ[key])
        # Obtain the SimpleCookie instance for the request.
        self.cookie = Cookie.SimpleCookie(self.environ.get('HTTP_COOKIE'))
        # Input: Handle according to content type and HTTP request method
        self.content_type = None
        self.content_type_params = dict()
        self.fields = cgi.FieldStorage() # Input parsed into CGI fields
        self.json = None                 # Input after JSON decoding
        self.data = None                 # Input as raw data
        if self.http_method == 'GET':
            self.handle_cgi_input()
        elif self.http_method == 'POST':
            self.handle_typed_input()
            # Allow override of HTTP method
            try:
                http_method = self.get_value('http_method')
                if not isinstance(http_method, basestring): raise KeyError
                http_method = http_method.strip()
                if not http_method: raise KeyError
            except KeyError:
                pass
            else:
                self.http_method = http_method
        elif self.http_method == 'PUT':
            self.handle_typed_input()

    def is_human_user_agent(self):
        "Guess whether the user agent represents a human, i.e. a browser."
        try:
            user_agent = self.environ['HTTP_USER_AGENT'].lower()
        except KeyError:
            pass
        else:
            for signature in self.HUMAN_USER_AGENT_SIGNATURES:
                if signature in user_agent:
                    return True
        return False

    def handle_cgi_input(self):
        self.fields = cgi.FieldStorage(environ=self.environ)

    def handle_typed_input(self):
        try:
            content_type = self.environ['CONTENT_TYPE']
        except KeyError:
            return
        content_type = mimeparse.parse_mime_type(content_type)
        self.content_type = "%s/%s" % content_type[0:2]
        self.content_type_params = content_type[2]
        if self.content_type in ('application/x-www-form-urlencoded',
                                 'multipart/form-data'):
            self.fields = cgi.FieldStorage(fp=self.environ['wsgi.input'],
                                           environ=self.environ)
        elif self.content_type == 'application/json':
            try:
                self.json = json.loads(self.environ['wsgi.input'].read())
            except ValueError:
                raise HTTP_BAD_REQUEST('invalid JSON')
        else:
            self.data = self.environ['wsgi.input'].read()

    def get_value(self, name):
        """Return the input item value by name.
        If input is CGI, FieldStorage.getvalue() is used;
        this returns None if the named field does not exist.
        If input is JSON, then uses ordinary dictionary lookup;
        an exception will be raised if the data is not a dictionary.
        If input is of some other type, raise KeyError.
        """
        if self.fields:
            return self.fields.getvalue(name)
        elif self.json:
            return self.json[name]
        else:
            raise KeyError('no named input items')
