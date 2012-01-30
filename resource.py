""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Handle access to a resource specified by the template URL path.
Resource, method and representation classes.

Methods subclass capabilities:

        fields    inrepr    outrepr
GET       yes       no        yes
HEAD      yes       no        no
POST      yes       yes       yes
PUT       no        yes       no
DELETE    no        no        no
"""

import logging
import re
import urllib
import cgi
import wsgiref.util
import wsgiref.headers

from .fields import *
from .response import *
from . import mimeparse
from .utils import HTTP_METHODS


class Resource(object):
    """Handle access to a resource specified by the template URL path.
    Container for the method function implementations.
    """

    def __init__(self, urlpath_template, type=None, descr=None, **methods):
        self.set_urlpath_template(urlpath_template)
        self._type = type
        self._descr = descr
        self.methods = dict()
        for key, instance in methods.items():
            if key not in HTTP_METHODS:
                raise ValueError("invalid HTTP method '%s'" % key)
            if not callable(instance):
                raise ValueError("HTTP method '%s' instance not callable" % key)
            self.methods[key] = instance

    @property
    def type(self):
        return self._type or self.__class__.__name__

    @property
    def descr(self):
        if self._descr:
            return self._descr
        try:
            get = self.methods['GET']
        except KeyError:
            return self.__doc__
        else:
            return get.descr

    def __str__(self):
        return "%s(%s)" % (self.type, self.urlpath_template)

    def __call__(self, request, application):
        self.url = wsgiref.util.request_uri(request.environ,include_query=False)
        format = self.variables.get('FORMAT')
        if format:
            self.url = self.url[0:-len(format)]
        try:
            method = self.methods[request.http_method]
        except KeyError:
            allow = ','.join(self.methods.keys())
            if request.http_method == 'OPTIONS':
                return HTTP_NO_CONTENT(Allow=allow)
            else:
                raise HTTP_METHOD_NOT_ALLOWED(Allow=allow)
        else:
            return method(self, request, application)

    def urlpath_template_match(self, urlpath):
        "Does the given URL path match this resource?"
        match = self.urlpath_matcher.match(urlpath)
        if match:
            self.variables = match.groupdict()
        else:
            self.variables = dict()
        return bool(match)

    _RX_VARIABLE = re.compile(r'\{([^/\}]+)\}')

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

    @staticmethod
    def _replace_variable(match):
        variable = match.group(1)
        try:
            variable, type = variable.split(':')
        except ValueError:
            expression = r'[^/]+?'
        else:
            if type == 'uuid':          # UUID with or without dashes
                expression = r'(?:[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})|(?:[a-f0-9]{32})'
            elif type == 'identifier':  # Identifier: alphabetical + word
                expression = r'[a-zA-Z_]\w*'
            elif type == 'integer':
                expression = r'[-+]?\d+'
            else:
                raise ValueError("unknown type in template variable: %s" % type)
        return "(?P<%s>%s)" % (variable, expression)

    def get_url(self, *segments, **query):
        """Synthesize an absolute URL from the resource URL
        and the given path segments and query.
        """
        url = '/'.join([self.url] + list(segments))
        if query:
            url += '?' + urllib.urlencode(query)
        return str(url)


class Method(object):
    """HTTP request method base class.
    An instance is callable, returning a response instance.
    """

    def __init__(self, descr=None):
        self._descr = descr

    @property
    def descr(self):
        if self._descr:
            return self._descr
        else:
            return self.__doc__

    def __call__(self, resource, request, application):
        "Handle the request and return a response instance."
        self.prepare(resource, request, application)
        try:
            self.handle(resource, request, application)
            return self.get_response(resource, request, application)
        finally:
            self.finalize()

    def prepare(self, resource, request, application):
        """Perform preparatory actions, e.g. login, or database connect.
        No actions by default.
        """
        pass

    def handle(self, resource, request, application):
        """Handle the request; perform actions according to the request.
        No actions by default.
        """
        pass

    def get_response(self, resource, request, application):
        "Return the response instance."
        raise NotImplementedError

    def finalize(self):
        """Perform finalization, e.g. database close.
        No actions by default.
        """
        pass


class FieldsMethodMixin(object):
    "Mixin class providing field handling methods."

    fields = ()
    
    def get_fields_data(self, fields=None, skip=set(),
                        default=dict(), fill=dict()):
        """Return the data for the fields to go into
        the 'form' entry of the resource data dictionary.
        If no fields are passed as argument, then use the fields
        defined at class level.
        """
        fields = fields or self.fields
        result = []
        for field in fields:
            if field.name in skip: continue
            result.append(field.get_data(default=default.get(field.name),
                                         fill=fill.get(field.name, dict())))
        return result

    def parse_fields(self, request, fields=None, skip=set()):
        """Return a dictionary containing the values for
        the input fields parsed out from the request.
        If no fields are passed as argument, then use the fields
        defined at class level.
        Raise HTTP_BAD_REQUEST if any problem.
        """
        fields = fields or self.fields
        result = dict()
        for field in fields:
            if field.name in skip: continue
            try:
                result[field.name] = field.get_value(request)
            except ValueError, msg:
                raise HTTP_BAD_REQUEST(str(msg))
        return result


class InreprsMethodMixin(object):
    "Mixin class providing incoming representation methods."

    inreprs = ()                      # List of Representation classes


class OutreprsMethodMixin(object):
    "Mixin class providing outgoing representation methods."

    outreprs = ()                     # List of Representation classes

    def get_response(self, resource, request, application):
        """Return the response instance.
        First, collect the data required for the representation.
        Then, decide which representation to use.
        Last, return the response from the representation given the data.
        """
        data = self.get_data(resource, request, application)
        outrepr = self.get_outrepr(resource, request, application)
        return outrepr(data)

    def get_data(self, resource, request, application):
        "Return a dictionary containing the data for the response."
        raise NotImplementedError

    def get_outrepr(self, resource, request, application):
        """Return the outgoing representation instance.
        Uses format or content negotiation using the Accept header
        to determine which outgoing representation to use.
        At least one outgoing representation must be defined.
        """
        if not self.outreprs:
            raise HTTP_NOT_ACCEPTABLE            
        # Hard request for output representation
        format = resource.variables.get('FORMAT')
        if format:
            format = format.lstrip('.')
            for outrepr in self.outreprs:
                if format == outrepr.format:
                    return outrepr()
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
                    return outrepr()
        # Fallback: choose the last; considered the most desirable
        return self.outreprs[-1]()

    def get_outrepr_links(self, resource, application, query=dict()):
        "Return data for links to all outreprs for the resource."
        url = resource.get_url()
        if url == application.url:
            url += '/'
        query = dict([(k,v) for k,v in query.iteritems() if v is not None])
        if query:
            query = '?' + urllib.urlencode(query)
        else:
            query = ''
        result = []
        for r in self.outreprs:
            result.append(dict(title=r.format.upper(),
                               mimetype=r.mimetype,
                               href=url + '.' + r.format + query))
        return result


class GET(FieldsMethodMixin, OutreprsMethodMixin, Method):
    pass

class HEAD(FieldsMethodMixin, Method):
    pass

class POST(FieldsMethodMixin, InreprsMethodMixin, OutreprsMethodMixin, Method):
    pass

class PUT(InreprsMethodMixin, Method):
    pass

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

    @property
    def descr(self):
        if self._descr:
            return self._descr
        else:
            return self.__doc__

    def __call__(self, data):
        "Return the response instance containing the representation."
        raise NotImplementedError
