""" wrapid: Web Resource API server framework built on Python WSGI.

Application class: WSGI interface.
"""

import logging
import re
import inspect
import urlparse
import traceback
import wsgiref.util
import wsgiref.headers

from .request import *
from .responses import *
from .utils import HTTP_METHODS, url_build


class Application(object):
    """An instance of this class, or a subclass thereof,
    is the Python WSGI interface to a web server.

    The web server must be configured to call an instance of
    this class for all HTTP requests to the relevant URLs.
    """

    # These should be modified in inheriting classes.
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
        self.path = urlparse.urlparse(self.url).path
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
            if inspect.isclass(method):
                method = method()
            response = method(request)
            return response(start_response)
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

    def add_resource(self, url_template, name=None, descr=None, **methods):
        "Define the HTTP method handlers for the given URL template."
        self.resources.append(Resource(url_template, name=name, descr=descr,
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
        pattern += '(?P<FORMAT>\.\w{1,4})?'
        pattern = "^%s$" % pattern
        self.urlpath_rx = re.compile(pattern)
        self.name = name
        self._descr = descr
        self.methods = dict()
        for key, method in methods.items():
            if key not in HTTP_METHODS:
                raise ValueError("invalid method '%s'" % key)
            if not (inspect.isclass(method) or inspect.isfunction(method)):
                raise ValueError("method '%s' is neither class nor function"
                                 % method)
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
        variable = match.group(1)
        try:
            variable, type = variable.split(':')
        except ValueError:
            expression = r'[^/]+'
        else:
            if type == 'uuid':          # UUID with or without dashes
                expression = r'(?:[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})|(?:[a-f0-9]{32})'
            elif type == 'identifier':  # Identifier: alphabetical + word
                expression = r'[a-zA-Z_]\w*'
            elif type == 'date':        # ISO date YYYY-MM-DD
                expression = r'\d{4}-\d{2}-\d{2}'
            elif type == 'integer':
                expression = r'[-+]?\d+'
            elif type == 'path':
                expression = r'.+'
            else:
                raise ValueError("unknown type in template variable: %s" % type)
        return "(?P<%s>%s)" % (variable, expression)
