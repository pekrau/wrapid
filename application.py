""" wrapid: Micro framework built on Python WSGI for RESTful server APIs

Application class: WSGI interface.
"""

import logging
import re
import inspect
import urlparse
import traceback
import wsgiref.util
import wsgiref.headers
import json

from .request import *
from .responses import *
from .utils import HTTP_METHODS, url_build


class Application(object):
    """An instance of this class, or a subclass thereof,
    is the Python WSGI interface to a web server.

    The web server must be configured to call an instance of
    this class for all HTTP requests to the relevant URLs.
    """

    # Default values used if none are provided at instantiation.
    version = 'x'
    host    = dict(title='web site',
                   href='http://localhost/',
                   admin='Administrator',
                   email='admin@localhost.xyz')
    debug   = False

    def __init__(self, name=None, version=None, host=None, debug=None):
        self.name = name or self.__class__.__name__
        self.version = version or self.version
        self.host = host or self.host
        self.debug = debug or self.debug
        self.resources = []
        self.url = None

    def __call__(self, environ, start_response):
        "WSGI interface; this method is called for each HTTP request."
        self.url = wsgiref.util.application_uri(environ)
        logging.debug("wrapid. Application URL %s", self.url)
        self.path = urlparse.urlparse(self.url).path
        logging.debug("wrapid: Application path %s", self.path)
        request = Request(environ)
        request.application = self
        logging.debug("wrapid: HTTP method '%s', URL path '%s'",
                      request.http_method,
                      request.urlpath)
        try:
            for resource in self.resources:
                match = resource.match(request.urlpath)
                if match:
                    request.name = resource.name
                    request.variables.update(match.groupdict())
                    break
            else:
                raise HTTP_NOT_FOUND
            request.remove_format_url()
            try:
                method = resource.methods[request.http_method]
            except KeyError:
                allow = ','.join(resource.methods.keys())
                if request.http_method == 'OPTIONS':
                    return HTTP_NO_CONTENT(Allow=allow)
                else:
                    raise HTTP_METHOD_NOT_ALLOWED(Allow=allow)
            try:
                self.prepare(request)
                if inspect.isfunction(method):
                    response = method(request)
                elif inspect.isclass(method):
                    response = method().respond(request)
                else:
                    raise ValueError('invalid HTTP request method handler')
                # Shortcut: If dict, then return as JSON representation
                if isinstance(response, dict):
                    data = json.dumps(response, indent=2)
                    response = HTTP_OK(content_type='application/json; charset=utf-8')
                    response.append(data)
                # Shortcut: If string, then either HTML or plain text
                elif isinstance(response, str):
                    data = response
                    # If first char '<', then HTML
                    if data[0] == '<':
                        response = HTTP_OK(content_type='text/html')
                    # If first char not '<', then plain text
                    else:
                        response = HTTP_OK(content_type='text/plain')
                    response.append(data)
                return response(start_response)
            finally:
                self.finalize(request)
        except HTTP_UNAUTHORIZED, error: # Do not log, nor give browser output
            logging.debug("wrapid: HTTP %s", error)
            return error(start_response)
        except HTTP_REDIRECTION, error:
            logging.debug("wrapid: HTTP %s", error)
            return error(start_response)
        except HTTP_ERROR, error:
            logging.debug("wrapid: HTTP %s", error)
            if request.human_user_agent:
                response = HTTP_OK(content_type='text/plain')
                response.append("%s\n\n%s" % (error, ''.join(error.content)))
                return response(start_response)
            else:
                return error(start_response)
        except Exception, message:
            tb = traceback.format_exc(limit=20)
            logging.error("wrapid: Exception\n%s", tb)
            error = HTTP_INTERNAL_SERVER_ERROR(content_type='text/plain')
            error.append("%s\n" % error)
            if self.debug:
                error.append('\n')
                error.append(tb)
            return error(start_response)

    def prepare(self, request):
        """Application-wide preparatory actions, e.g. database connect.
        No action by default.
        """
        pass

    def finalize(self, request):
        """Application-wide finalizin actions, e.g. database close..
        No action by default.
        """
        pass

    def add_resource(self, url_template, name=None, descr=None, **methods):
        "Define the HTTP method handlers for the given URL template."
        self.resources.append(Resource(url_template,
                                       name=name,
                                       descr=descr,
                                       **methods))

    def get_url(self, *segments, **query):
        """Synthesize an absolute URL from the application URL
        and the given path segments and query.
        """
        assert self.url
        segments = [self.url] + list(segments)
        return url_build(*segments, **query)


class Resource(object):
    """Handle access to a resource specified by the template URL path.
    Container for the HTTP method handlers.
    """

    VARIABLE_RX = re.compile(r'\{([^/\}]+)\}')

    def __init__(self, urlpath_template, name=None, descr=None, **methods):
        self.urlpath_template = urlpath_template
        if urlpath_template in ['', '/']: # Special cases
            pattern = '/?'
        else:
            pattern = urlpath_template
        pattern = self.VARIABLE_RX.sub(self.replace_variable, pattern)
        pattern += r'(?P<FORMAT>\.\w{1,4})?'
        pattern = "^%s$" % pattern
        self.urlpath_rx = re.compile(pattern)
        self.name = name
        self._descr = descr
        self.methods = dict()
        for key, method in methods.items():
            if key not in HTTP_METHODS:
                raise ValueError("invalid method '%s'" % key)
            if inspect.isfunction(method):
                pass
            elif inspect.isclass(method):
                if not hasattr(method, 'respond'):
                    raise ValueError("method '%s' implementation class '%s'"
                                     " lacks 'respond' method"
                                     % (key, method))
            self.methods[key] = method

    def __str__(self):
        return "%s (%s)" % (self.name, self.urlpath_template)

    def match(self, urlpath):
        return self.urlpath_rx.match(urlpath)

    @property
    def descr(self):
        if self._descr:
            return self._descr
        for key in HTTP_METHODS:
            try:
                return self.methods[key].__doc__
            except KeyError:
                pass
        return None

    def replace_variable(self, match):
        "Replace the variable specification with a regexp."
        variable = match.group(1)
        try:
            variable, type = variable.split(':')
        except ValueError:              # Any characters in a segment
            expression = r'[^/]+?'
        else:
            if type == 'uuid':          # UUID with or without dashes
                expression = r'(?:[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})|(?:[a-f0-9]{32})'
            elif type == 'identifier':  # Identifier: alphabetical + word
                expression = r'[a-zA-Z_]\w*?'
            elif type == 'date':        # ISO date YYYY-MM-DD
                expression = r'\d{4}-\d{2}-\d{2}'
            elif type == 'integer':     # Integer, optionally with sign
                expression = r'[-+]?\d+'
            elif type == 'path':        # Any characters, ignore segmentation
                expression = r'.+?'
            else:
                raise ValueError("unknown type in template variable: %s" % type)
        return "(?P<%s>%s)" % (variable, expression)
