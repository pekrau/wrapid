""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Example web service.
"""

import logging
import os.path

logging.basicConfig(level=logging.DEBUG)

import wrapid
from wrapid.application import Application
from wrapid.resource import *
from wrapid.response import *
from wrapid.get_static import GET_Static
from wrapid.utils import basic_authentication
from wrapid.get_documentation import GET_Documentation
from wrapid.html_representation import markdown_to_html
from wrapid.json_representation import JsonRepresentation


DIRPATH = os.path.dirname(__file__)


def home(resource, request, application):
    "Home page for the web application."
    response = HTTP_OK(content_type='text/html')
    try:
        infile = open(os.path.join(DIRPATH, 'README.md'))
    except IOError:
        readme = 'Error: could not find the README.rd file'
    else:
        readme = markdown_to_html(infile.read())
        infile.close()
    lookup = dict(baseurl=application.url,
                  version=wrapid.__version__,
                  readme=readme,
                  scilifelab='http://tools.scilifelab.se/wrapid')
    response.append("""
<html>
<title>wrapid %(version)s example</title>
<body>
<h1>wrapid %(version)s example</h1>
<p>
%(readme)s
</p>
<h2>Example resources</h2>
<ul>
<li> <a href='%(baseurl)s/login'>Login</a>: Basic Authentication for a name and password.
<li> <a href='%(baseurl)s/crash'>Crash</a>: Force a server crash.
<li> <a href='%(baseurl)s/debug'>Debug</a>: Output debug information; CGI info.
<li> <a href='%(baseurl)s/doc'>Doc</a>: Produce documentation of the API for
     this web resource by introspection.
</ul>
</body>
</html>
""" % lookup)
    return response
home.mimetype = 'text/html'

def login(resource, request, application):
    "Require user name and password."
    user, password = basic_authentication(request, 'wrapid')
    response = HTTP_OK(content_type='text/plain')
    response.append("User: %s\n" % user)
    response.append("Password: %s\n" % password)
    return response

def crash(resource, request, application):
    "Force an internal server error."
    response = HTTP_OK(content_type='text/plain')
    response.append('This is a forced crash.\n')
    raise ValueError('explicitly forced error')

def debug(resource, request, application):
    "Return information about the request data provided to the server."
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
debug.mimetype = 'text/plain'


class Factory(POST):
    "Here POST method documentation should go."

    outreprs = (JsonRepresentation,)

    fields = (TextField('thing',
                        required=True,
                        descr='Thing to make.'),)

    def get_data(self, resource, request, application):
        return dict(info='some data')


class WrapidExample(Application):
    version = wrapid.__version__
    debug   = True

application = WrapidExample()

application.append(Resource('/', type='Home', GET=home))
application.append(Resource('/login', type='Login', GET=login))
application.append(Resource('/crash', type='Crash', GET=crash))
application.append(Resource('/debug', type='Debug', GET=debug))

application.append(Resource('/static/{filename}', type='File',
                            GET=GET_Static(os.path.join(DIRPATH, 'static'))))

application.append(Resource('/factory', type='Factory',
                            POST=Factory()))

application.append(Resource('/doc', type='Documentation',
                            GET=GET_Documentation()))
