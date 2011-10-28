"""wrapid: Web Resource Application Programming Interface built on Python WSGI.

Handle access to a resource specified by the template URL path.
Resource, request method and output representation classes.
"""

import logging
import re
import urllib
import cgi
import wsgiref.util
import wsgiref.headers

from . import utils
from .response import *
from . import mimeparse


HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE']


class Resource(object):
    """Handle access to a resource specified by the template URL path.
    Container for the method function implementations.
    """

    def __init__(self, urlpath_template, name=None, descr=None, **methods):
        self.set_urlpath_template(urlpath_template)
        self._name = name
        self._descr = descr
        self.methods = dict()
        for key, instance in methods.items():
            if key not in HTTP_METHODS:
                raise ValueError("invalid HTTP method '%s'" % key)
            if not callable(instance):
                raise ValueError("HTTP method '%s' instance not callable" % key)
            self.methods[key] = instance

    @property
    def name(self):
        return self._name or self.__class__.__name__

    def descr(self):
        if self._descr:
            return self._descr
        try:
            get = self.methods['GET']
        except KeyError:
            return self.__doc__
        else:
            try:
                return get.descr()
            except (TypeError, AttributeError):
                return get.__doc__

    def __str__(self):
        return "%s(%s)" % (self.name, self.urlpath_template)

    def __call__(self, request, application):
        self.url = wsgiref.util.request_uri(request.environ,include_query=False)
        format = self.variables.get('FORMAT')
        if format:
            self.url = self.url[0:-len(format)]
        try:
            method = self.methods[request.http_method]
        except KeyError:
            raise HTTP_METHOD_NOT_ALLOWED(allow=','.join(self.methods.keys()))
        else:
            return method(self, request, application)

    def urlpath_template_match(self, urlpath):
        "Does the given URL path match this resource?"
        match = self.urlpath_matcher.match(urlpath)
        if match:
            self.variables = match.groupdict()
            logging.debug("wrapid: URL variables: %s", self.variables)
        else:
            self.variables = dict()
        return bool(match)

    def set_urlpath_template(self, urlpath_template):
        "Set the URL path template and the compiled regexp."
        self.urlpath_template = urlpath_template
        if urlpath_template in ['', '/']: # Special cases
            pattern = '/?'
        else:
            pattern = urlpath_template
        pattern = self._RX_VARIABLE.sub(self._replace_variable, pattern)
        pattern += '(?P<FORMAT>\.\w{1,4})?'
        pattern = "^%s$" % pattern
        self.urlpath_matcher = re.compile(pattern)

    _RX_VARIABLE = re.compile(r'\{([^/\}]+)\}')

    @staticmethod
    def _replace_variable(match):
        return "(?P<%s>[^/]+?)" % match.group(1)

    def get_url(self, *segments, **query):
        """Synthesize an absolute URL from the resource URL
        and the given path segments and query.
        """
        url = '/'.join([self.url] + list(segments))
        if query:
            url += '?' + urllib.urlencode(query)
        return str(url)


class Method(object):
    """Base abstract class for executing the HTTP request method on a resource.
    A call on an instance must return a response instance.
    """

    def __init__(self, descr=None):
        self._descr = descr

    def descr(self):
        if self._descr:
            return self._descr
        else:
            return self.__doc__

    def __call__(self, resource, request, application):
        "Handle the request and return a response instance."
        raise NotImplementedError

    def get_outreprs_links(self, resource, request, application):
        "Return dictionaries for links to all outreprs for the resource."
        return None


class GET(Method):
    "HTTP request method GET."

    def __init__(self, outreprs=[], infields=None, descr=None):
        """At least one output representation must be specified.
        The 'infields' argument must be a Fields instance.
        """
        super(GET, self).__init__(descr=descr)
        self.outreprs = outreprs[:]
        self.infields = infields

    def __call__(self, resource, request, application):
        """Handle the request and return a response instance.
        Retrieve the data to display, and create the response from it.
        Use format or content negotiation using the Accept header
        to determine which outgoing representation to use.
        """
        data = self.get_data(resource, request, application)
        if not self.outreprs:
            raise HTTP_NOT_ACCEPTABLE            

        # Hard request for output representation
        format = resource.variables.get('FORMAT')
        if format:
            format = format.lstrip('.')
            for outrepr in self.outreprs:
                if format == outrepr.format:
                    return outrepr(data)
            else:
                raise HTTP_NOT_ACCEPTABLE

        # Output representation content negotiation
        accept = request.headers['Accept']
        if accept:
            supported = [r.mimetype for r in self.outreprs]
            mimetype = mimeparse.best_match(supported, accept)
            if not mimetype:
                raise HTTP_NOT_ACCEPTABLE            
            for outrepr in self.outreprs:
                if mimetype == outrepr.mimetype:
                    return outrepr(data)

        # Fallback: choose the most desirable according to order
        return self.outreprs[-1](data)

    def get_data(self, resource, request, application):
        """Return the data to display as a data structure
        for the response generator to interpret.
        """
        raise NotImplementedError

    def get_outreprs_links(self, resource, request, application):
        "Return data for links to all outreprs for the resource."
        url = resource.get_url()
        if url == application.url:
            url += '/'
        result = []
        for r in self.outreprs:
            result.append(dict(title=r.format.upper(),
                               mimetype=r.mimetype,
                               href=url + '.' + r.format))
        return result


class POST(Method):
    "HTTP request method POST."

    def __init__(self, inreprs=[], outreprs=[], infields=None, descr=None):
        """Zero or more input representations may be specified.
        The 'infields' argument must be a Fields instance.
        """
        super(POST, self).__init__(descr=descr)
        self.inreprs = inreprs[:]
        self.outreprs = outreprs[:]
        self.infields = infields


class PUT(Method):
    "HTTP request method PUT."

    def __init__(self, inreprs=[], outreprs=[], descr=None):
        super(PUT, self).__init__(descr=descr)
        self.inreprs = inreprs[:]
        self.outreprs = outreprs[:]


class DELETE(Method):
    pass


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

    def descr(self):
        if self._descr:
            return self._descr
        else:
            return self.__doc__

    def __call__(self, data):
        "Return the response instance containing the representation."
        raise NotImplementedError


class DummyRepresentation(Representation):

    def __init__(self, mimetype, descr):
        self.mimetype = mimetype
        self._descr = descr
