""" wrapid: Web Resource API server framework built on Python WSGI.

Example web service, illustrating use of the wrapid package.
"""

import logging
import os.path
import csv
from cStringIO import StringIO

logging.basicConfig(level=logging.DEBUG)

import wrapid
from wrapid.fields import *
from wrapid.response import *
from wrapid.application import Application
from wrapid.resource import Resource, GET, POST
from wrapid.static import *
from wrapid.documentation import *
from wrapid.html_representation import * # Warning: potential 'HEAD' collision!
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation


DIR_PATH = os.path.dirname(__file__)


class MethodMixin(object):
    "Mixin class providing the links data for all HTTP method classes."

    def get_data_links(self, resource, request, application):
        "Return the links data for the response."
        return [dict(title='Debug',
                     href=application.get_url('debug')),
                dict(title='Crash',
                     href=application.get_url('crash')),
                dict(title='Input',
                     href=application.get_url('input')),
                dict(title='Documentation: API',
                     href=application.get_url('doc'))]


class HomeHtmlRepresentation(BaseHtmlRepresentation):
    stylesheets = ['static/standard.css']


class GET_Home(MethodMixin, GET):
    "Home page for the web application."

    outreprs = [TextRepresentation,
                JsonRepresentation,
                HomeHtmlRepresentation]

    def get_data_resource(self, resource, request, application):
        "Return the data dictionary for the response."
        try:
            descr = open(os.path.join(DIR_PATH, 'README.md')).read()
        except IOError:
            descr = 'Error: Could not find the wrapid README.rd file.'
        return dict(descr=descr)


class ApiDocumentationHtmlRepresentation(ApiDocumentationHtmlMixin,
                                         BaseHtmlRepresentation):
    stylesheets = ['static/standard.css']


class GET_WrapidApiDocumentation(MethodMixin, GET_ApiDocumentation):
    "Produce the documentation for the web resource API by introspection."

    outreprs = [TextRepresentation,
                JsonRepresentation,
                ApiDocumentationHtmlRepresentation]


class FormHtmlRepresentation(FormHtmlMixin, BaseHtmlRepresentation):
    stylesheets = ['static/standard.css']

    def get_descr(self):
        table = TABLE(border=1)
        for row in self.data.get('rows', []):
            table.append(TR(*[TD(i) for i in row]))
        return table


class GET_Input(MethodMixin, GET):

    outreprs = [TextRepresentation,
                JsonRepresentation,
                FormHtmlRepresentation]

    fields = (SelectField('delimiter',
                          required=True,
                          options=['tab', 'comma'],
                          default='tab',
                          boxes=True),
              TextField('text', required=True,
                        descr='Delimited text for table.'))

    def get_data_resource(self, resource, request, application):
        return dict(title='Input',
                    descr='Test input of text to be parsed into tabular form,'
                    ' row by row using a delimiter (tab or comma).',
                    form=dict(title='Input text',
                              fields=self.get_data_fields(),
                              href=resource.url,
                              cancel=application.url))

class POST_Input(MethodMixin, POST):

    outreprs = [TextRepresentation,
                JsonRepresentation,
                FormHtmlRepresentation]

    fields = GET_Input.fields

    def handle(self, resource, request, application):
        values = self.parse_fields(request)
        if values['delimiter'] == 'comma':
            delimiter = ','
        else:
            delimiter = '\t'
        reader = csv.reader(StringIO(values.get('text', '[no text')),
                            delimiter=delimiter)
        self.rows = list(reader)

    def get_data_resource(self, resource, request, application):
        return dict(title='Input',
                    rows=self.rows,
                    form=dict(title='Paste in text',
                              fields=self.get_data_fields(),
                              href=resource.url,
                              quit=application.url))


def debug(resource, request, application):
    "Return information about the request data. Function for HTTP method."
    response = HTTP_OK(content_type='text/plain')
    response.append("Application URL: %s\n" % application.url)
    response.append("   Resource URL: %s\n\n" % resource.url)
    response.append('HTTP headers\n------------\n\n')
    for item in sorted(request.headers.items()):
        response.append("%s: %s\n" % item)
    response.append('\nenviron\n-------\n\n')
    for item in sorted(request.environ.items()):
        response.append("%s: %s\n" % item)
    return response

debug.mimetype = 'text/plain'           # Func attr to specify mimetype

def crash(resource, request, application):
    "Force an internal server error. Function for HTTP method."
    response = HTTP_OK(content_type='text/plain')
    response.append('This response will not be returned.')
    raise ValueError('explicitly forced error')



application = Application(name='Wrapid example',
                          version=wrapid.__version__,
                          host=dict(title='web site',
                                    href='http://localhost/',
                                    admin='Administrator',
                                    email='admin@dummy.xyz'),
                          debug=True)


application.append(Resource('/', type='Home', GET=GET_Home))
application.append(Resource('/debug', type='Debug', GET=debug))
application.append(Resource('/crash', type='Crash', GET=crash))
application.append(Resource('/input', type='Input',
                            GET=GET_Input,
                            POST=POST_Input))
application.append(Resource('/static/{filename}', type='File',
                            GET=GET_Static(DIR_PATH)))
application.append(Resource('/doc', type='Documentation API',
                            GET=GET_WrapidApiDocumentation))
