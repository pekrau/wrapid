""" wrapid: Web Resource API server framework built on Python WSGI.

Example web service, illustrating use of the wrapid package.
"""

import logging
import os.path
import csv
from cStringIO import StringIO

logging.basicConfig(level=logging.DEBUG)

import wrapid
from wrapid.application import *
from wrapid.methods import *
from wrapid.file import *
from wrapid.documentation import *
from wrapid.html_representation import * # Warning: potential 'HEAD' collision!
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation


class MethodMixin(object):
    "Mixin class providing the links data for all HTTP method classes."

    def get_data_links(self, request):
        "Return the links data for the response."
        return [dict(title='Debug',
                     href=request.application.get_url('debug')),
                dict(title='Crash',
                     href=request.application.get_url('crash')),
                dict(title='Input',
                     href=request.application.get_url('input')),
                dict(title='Documentation: API',
                     href=request.application.get_url('doc'))]


class HomeHtmlRepresentation(BaseHtmlRepresentation):
    stylesheets = ['static/standard.css']


class Home(MethodMixin, GET):
    "Home page for the web application."

    outreprs = [TextRepresentation,
                JsonRepresentation,
                HomeHtmlRepresentation]

    def get_data_resource(self, request):
        "Return the data dictionary for the response."
        try:
            dirpath = os.path.dirname(__file__)
            descr = open(os.path.join(dirpath, 'README.md')).read()
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
    "Display page for input of TAB- or comma-delimited text."

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

    def get_data_resource(self, request):
        return dict(title='Input',
                    descr='Test input of text to be parsed into tabular form,'
                    ' row by row using a delimiter (tab or comma).',
                    form=dict(title='Input text',
                              fields=self.get_data_fields(),
                              href=request.url,
                              cancel=request.application.url))

class POST_Input(MethodMixin, POST):
    "Display results, and page for input of TAB- or comma-delimited text."

    outreprs = [TextRepresentation,
                JsonRepresentation,
                FormHtmlRepresentation]

    fields = GET_Input.fields

    def process(self, request):
        values = self.parse_fields(request)
        if values['delimiter'] == 'comma':
            delimiter = ','
        else:
            delimiter = '\t'
        reader = csv.reader(StringIO(values.get('text', '[no text')),
                            delimiter=delimiter)
        self.rows = list(reader)

    def get_data_resource(self, request):
        return dict(title='Input',
                    rows=self.rows,
                    form=dict(title='Paste in text',
                              fields=self.get_data_fields(),
                              href=request.url,
                              quit=request.application.url))


def debug(request):
    "Return information about the request data. Function for HTTP method."
    response = HTTP_OK(content_type='text/plain')
    response.append("Application URL: %s\n" % request.application.url)
    response.append("   Resource URL: %s\n\n" % request.url)
    response.append('HTTP headers\n------------\n\n')
    for item in sorted(request.headers.items()):
        response.append("%s: %s\n" % item)
    response.append('\nenviron\n-------\n\n')
    for item in sorted(request.environ.items()):
        response.append("%s: %s\n" % item)
    return response

debug.mimetype = 'text/plain'           # Func attr to specify mimetype

def crash(request):
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


application.add_resource('/', name='Home', GET=Home)
application.add_resource('/debug', name='Debug', GET=debug)
application.add_resource('/crash', name='Crash', GET=crash)
application.add_resource('/input', name='Input',
                         GET=GET_Input,
                         POST=POST_Input)

class GET_File_static(GET_File):
    dirpath = os.path.dirname(__file__)

application.add_resource('/static/{filename}', name='File',
                         GET=GET_File_static)
application.add_resource('/doc', name='Documentation API',
                         GET=GET_WrapidApiDocumentation)
