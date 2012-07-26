""" wrapid: Micro framework built on Python WSGI for RESTful server APIs

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
from wrapid.file import File
from wrapid.documentation import *
from wrapid.html_representation import * # Warning: potential 'HEAD' collision!
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation
from wrapid.xml_representation import XmlRepresentation


class MethodMixin(object):
    "Mixin class providing the links data for all HTTP method classes."

    def get_data_links(self, request):
        "Return the navigation links data."
        return [dict(title='Text',
                     href=request.application.get_url('text')),
                dict(title='HTML',
                     href=request.application.get_url('html')),
                dict(title='JSON',
                     href=request.application.get_url('json')),
                dict(title='Input',
                     href=request.application.get_url('input')),
                dict(title='Crash',
                     href=request.application.get_url('crash')),
                dict(title='Debug',
                     href=request.application.get_url('debug'))]

    def get_data_documentation(self, request):
        "Return the documentation links data."
        return [dict(title='API',
                     href=request.application.get_url('doc'))]


class HomeHtmlRepresentation(BaseHtmlRepresentation):
    stylesheets = ['static/standard.css']


class Home(MethodMixin, GET):
    "Home page for the web application."

    outreprs = [JsonRepresentation,
                TextRepresentation,
                HomeHtmlRepresentation]

    def get_data_resource(self, request):
        "Return the data dictionary for the response."
        try:
            dirpath = os.path.dirname(__file__)
            descr = open(os.path.join(dirpath, 'README.md')).read()
        except IOError:
            return dict(descr='Error: Could not find the README.rd file.',
                        resource='Home')
        else:
            descr = descr.split('\n')
            return dict(title=descr[0],
                        resource='Home',
                        descr='\n'.join(descr[3:]))


class ApiDocumentationHtmlRepresentation(ApiDocumentationHtmlMixin,
                                         BaseHtmlRepresentation):
    stylesheets = ['static/standard.css']


class ApiDocumentation(MethodMixin, GET_ApiDocumentation):
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
                XmlRepresentation,
                FormHtmlRepresentation]

    fields = (SelectField('delimiter',
                          required=True,
                          options=['tab', 'comma'],
                          default='comma',
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


def text(request):
    """Simplest possible way of outputting plain text.
    The first character cannot be a '<', else it will
    be output as HTML."""
    return 'This is some plain text.'

def html(request):
    """Simplest possible way of outputting HTML.
    The first character must be a '<' for the string
    to be output as HTML."""
    return '''<!doctype html>
<meta charset=utf-8>
<h1>HTML</h1>
<p>This is some HTML5 text.</p>'''

def json(request):
    """Simplest possible way of outputting JSON.
    The returned value must be a dictionary containing
    only predefined Python data types."""
    return dict(title='JSON data',
                something='Some data',
                integers=[1, -3, 10945],
                lookup={'thingy': 'stuff'})

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


application = Application(name='Wrapid',
                          version=wrapid.__version__,
                          debug=True)


application.add_resource('/', name='Home', GET=Home)
application.add_resource('/text', name='Text', GET=text)
application.add_resource('/html', name='HTML', GET=html)
application.add_resource('/json', name='JSON', GET=json)
application.add_resource('/input',
                         name='Input',
                         GET=GET_Input,
                         POST=POST_Input)
application.add_resource('/crash', name='Crash', GET=crash)
application.add_resource('/debug', name='Debug', GET=debug)


class StaticFile(File):
    "Return the specified file from a predefined server directory."
    dirpath = os.path.dirname(__file__)
    charset = 'utf-8'

application.add_resource('/static/{filepath}',
                         name='File',
                         GET=StaticFile)
application.add_resource('/doc',
                         name='Documentation API',
                         GET=ApiDocumentation)
