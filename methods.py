""" wrapid: Web Resource API server framework built on Python WSGI.

HTTP method classes for handling access to a resource.

Methods subclass capabilities:

        fields    inrepr    outrepr
GET       yes       no        yes
HEAD      yes       no        no
POST      yes       yes       yes
PUT       no        yes       no
DELETE    no        no        no
"""

import logging

from .fields import *
from .responses import *
from . import mimeparse


class Method(object):
    """HTTP request method abstract base class.
    An instance is callable, returning a response instance.
    """

    def __call__(self, request):
        "Handle the request and return a response instance."
        self.prepare(request)
        try:
            self.handle(request)
            return self.get_response(request)
        finally:
            self.finalize()

    def prepare(self, request):
        """Perform preparatory actions, e.g. login, or database connect.
        No actions by default.
        """
        pass

    def handle(self, request):
        """Handle the request; perform actions according to the request.
        No actions by default.
        """
        pass

    def get_response(self, request):
        "Return the response instance."
        raise NotImplementedError

    def finalize(self):
        """Perform finalization, e.g. database close.
        No actions by default.
        """
        pass


class FieldsMethodMixin(object):
    "Mixin class providing field handling functions."

    fields = ()
    
    def get_data_fields(self, fields=None, skip=set(), override=dict()):
        """Return the data for the fields to go into the 'form' entry
        of the resource data dictionary.
        If no fields are passed as argument, then the fields defined
        at class level are used.
        The 'override' dictionary contains parameter values to override
        those set for each Field instance.
        """
        fields = fields or self.fields
        result = []
        for field in fields:
            if field.name in skip: continue
            result.append(field.get_data(override=override.get(field.name,
                                                               dict())))
        return result

    def parse_fields(self, request, fields=None, skip=set(), additional=[]):
        """Return a dictionary containing the values for the input fields
        parsed out from the request.
        If no fields are passed as argument, then the fields defined
        at class level are used.
        Raise HTTP_BAD_REQUEST if any problem.
        """
        fields = fields or self.fields
        fields = [f for f in fields if f.name not in skip]
        fields.extend(additional)
        result = dict()
        for field in fields:
            try:
                result[field.name] = field.get_value(request, self)
            except ValueError, msg:
                raise HTTP_BAD_REQUEST(str(msg))
        return result


class InreprsMethodMixin(object):
    "Mixin class providing incoming representation functions."

    inreprs = ()                      # List of Representation classes


class OutreprsMethodMixin(object):
    "Mixin class providing outgoing representation functions."

    outreprs = ()                     # List of Representation classes

    def get_response(self, request):
        """Return the response instance.
        First collect the data required for the representation.
        Then decide which representation to use.
        Lastly return the response from the representation given the data.
        """
        data = self.get_data(request)
        outrepr = self.get_outrepr(request)
        return outrepr(data)

    def get_data(self, request):
        "Return the response data dictionary."
        data               = self.get_data_general(request)
        data['links']      = self.get_data_links(request)
        data['operations'] = self.get_data_operations(request)
        data['outreprs']   = self.get_data_outreprs(request)
        data.update(self.get_data_resource(request))
        return data

    def get_data_general(self, request):
        "Return the general response data dictionary."
        data = dict(application=dict(name=request.application.name,
                                     version=request.application.version,
                                     href=request.application.url,
                                     host=request.application.host),
                    title="%s %s" % (request.application.name,
                                     request.application.version),
                    href=request.url)
        # This works with LoginMixin, if used.
        try:
            data['login'] = self.login['name']
        except AttributeError:
            pass
        return data

    def get_data_links(self, request):
        "Return the links response data."
        return []

    def get_data_operations(self, request):
        "Return the operations response data."
        return []

    def get_data_outreprs(self, request):
        "Return the outrepr links response data."
        url = request.url
        if url == request.application.url:
            url += '/'
        outreprs = []
        for outrepr in self.outreprs:
            outreprs.append(dict(title=outrepr.format.upper(),
                                 mimetype=outrepr.mimetype,
                                 href=url + '.' + outrepr.format))
        return outreprs

    def get_data_resource(self, request):
        "Return the dictionary with the resource-specific response data."
        return dict()

    def get_outrepr(self, request):
        """Return the outgoing representation instance.
        Does format or content negotiation using the Accept header
        to determine which outgoing representation to use.
        At least one outgoing representation must be defined.
        """
        if not self.outreprs:
            raise HTTP_NOT_ACCEPTABLE            
        # Hard request for output representation
        format = request.variables.get('FORMAT')
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

    def get_response(self, request):
        "Redirect to a URL specified by the attribute 'redirect'."
        return HTTP_SEE_OTHER(Location=self.redirect)
