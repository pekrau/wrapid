""" wrapid: Web Resource API server framework built on Python WSGI.

Resource and HTTP method classes for handling access to a resource.

Methods subclass capabilities:

        fields    inrepr    outrepr
GET       yes       no        yes
HEAD      yes       no        no
POST      yes       yes       yes
PUT       no        yes       no
DELETE    no        no        no
"""

import re
import cgi
import inspect
import wsgiref.util

from .fields import *
from .response import *
from . import mimeparse
from .utils import HTTP_METHODS, url_build


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
            if inspect.isclass(instance): # If class, then instantiate
                instance = instance()
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
        for key in HTTP_METHODS:
            try:
                method = self.methods[key]
            except KeyError:
                pass
            else:
                try:
                    return method.descr
                except AttributeError:
                    return method.__doc__
        else:
            return None

    def __str__(self):
        return "%s(%s)" % (self.type, self.urlpath_template)

    def __call__(self, request, application):
        "Dispatch the request to the indicated HTTP method instance."
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
            elif type == 'date':        # ISO date YYYY-MM-DD
                expression = r'\d{4}-\d{2}-\d{2}'
            elif type == 'integer':
                expression = r'[-+]?\d+'
            else:
                raise ValueError("unknown type in template variable: %s" % type)
        return "(?P<%s>%s)" % (variable, expression)

    def undo_format_specifier(self, varname):
        """It has been determined in some way that the FORMAT specifier
        in the URL really is part of the resource identifier,
        so undo the split by appending the FORMAT part to the variable
        of the given name.
        """
        self.variables[varname] += self.variables['FORMAT']
        self.url += self.variables['FORMAT']
        self.variables['FORMAT'] = None

    def get_url(self, *segments, **query):
        """Synthesize an absolute URL from the resource URL
        and the given path segments and query.
        """
        segments = [self.url] + list(segments)
        return url_build(*segments, **query)


class Method(object):
    """HTTP request method abstract base class.
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
        First collect the data required for the representation.
        Then decide which representation to use.
        Lastly return the response from the representation given the data.
        """
        data = self.get_data(resource, request, application)
        outrepr = self.get_outrepr(resource, request, application)
        return outrepr(data)

    def get_data(self, resource, request, application):
        "Return the response data dictionary."
        data = self.get_data_general(resource, request, application)
        data['links'] = \
            self.get_data_links(resource, request, application)
        data['operations'] = \
            self.get_data_operations(resource, request, application)
        data['outreprs'] = \
            self.get_data_outreprs(resource, request, application)
        data.update(self.get_data_resource(resource, request, application))
        return data

    def get_data_general(self, resource, request, application):
        "Return the general response data dictionary."
        data = dict(application=dict(name=application.name,
                                     version=application.version,
                                     href=application.url,
                                     host=application.host),
                    title="%s %s" % (application.name, application.version),
                    resource=resource.type,
                    href=resource.url)
        # This works with LoginMixin, if used.
        try:
            data['login'] = self.login['name']
        except AttributeError:
            pass
        return data

    def get_data_links(self, resource, request, application):
        "Return the links response data."
        return []

    def get_data_operations(self, resource, request, application):
        "Return the operations response data."
        return []

    def get_data_outreprs(self, resource, request, application):
        "Return the outrepr links response data."
        url = resource.url
        if url == application.url:
            url += '/'
        outreprs = []
        for outrepr in self.outreprs:
            outreprs.append(dict(title=outrepr.format.upper(),
                                 mimetype=outrepr.mimetype,
                                 href=url + '.' + outrepr.format))
        return outreprs

    def get_data_resource(self, resource, request, application):
        "Return the dictionary with the resource-specific response data."
        return dict()

    def get_outrepr(self, resource, request, application):
        """Return the outgoing representation instance.
        Does format or content negotiation using the Accept header
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


class RedirectMixin(object):
    "Mixin class for HTTP method classes, providing a redirect response."

    def set_redirect(self, url):
        self.redirect = url

    def get_response(self, resource, request, application):
        "Redirect to a URL specified by the attribute 'redirect'."
        return HTTP_SEE_OTHER(Location=self.redirect)
