""" wrapid: Web Resource API server framework built on Python WSGI.

Request class: data container for a single request.
"""

import logging
import cgi
import json
import Cookie
import wsgiref.util
import wsgiref.headers

from . import mimeparse
from .utils import url_build


class Request(object):
    "Data container for a single HTTP request."

    # The values must be in lower case.
    HUMAN_USER_AGENT_SIGNATURES = ['mozilla', 'firefox', 'opera',
                                   'chrome', 'safari', 'msie']

    def __init__(self, environ):
        "Standard setup of attributes from the HTTP input data."
        self.environ = environ.copy()
        self.url = wsgiref.util.request_uri(self.environ, include_query=False)
        self.urlpath = self.environ['PATH_INFO']
        self.http_method = self.environ['REQUEST_METHOD']
        self.name = None
        self.variables = dict()
        self.human_user_agent = self.is_human_user_agent()
        # Obtain the HTTP headers for the request.
        self.headers = wsgiref.headers.Headers([])
        for key, value in self.environ.iteritems():
            if key.startswith('HTTP_'):
                name = '-'.join([p.capitalize() for p in key[5:].split('_')])
                self.headers[name] = str(value)
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
                self.http_method = http_method
            except KeyError:
                pass
        elif self.http_method == 'PUT':
            self.handle_typed_input()

    def remove_format_url(self):
        "Remove the format part of the URL, if any."
        format = self.variables.get('FORMAT')
        if format:
            self.url = self.url[0:-len(format)]

    def undo_format_specifier(self, varname):
        """The application code has determined that the FORMAT specifier in
        the URL really is part of the resource identifier, so undo the split
        by appending the FORMAT part to the variable of the given name.
        """
        self.variables[varname] += self.variables['FORMAT']
        self.url += self.variables['FORMAT']
        self.variables['FORMAT'] = None

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
        logging.debug("wrapid: incoming content type: %s", self.content_type)
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

    def get_url(self, *segments, **query):
        """Synthesize an absolute URL from the URL for this request
        and the given path segments and query.
        """
        segments = [self.url] + list(segments)
        return url_build(*segments, **query)
