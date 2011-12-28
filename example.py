""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Example web service.
"""

import logging
import os.path

logging.basicConfig(level=logging.DEBUG)

from wrapid import __version__
from wrapid.application import Application
from wrapid.resource import *
from wrapid.fields import *
from wrapid.response import *
from wrapid.utils import basic_authentication
from wrapid.get_documentation import GET_Documentation
from wrapid.get_static import GET_Static


def root(resource, request, application):
    "Home page for the web application."
    response = HTTP_OK(content_type='text/html')
    lookup = dict(baseurl=application.url,
                  github='https://github.com/pekrau/wrapid',
                  scilifelab='http://tools.scilifelab.se/wrapid')
    response.append("""
<html>
<title>wrapid example</title>
<body>
<h1>wrapid example</h1>
<p>
wrapid: Web Resource Application Programming Interface built on Python WSGI.

</p>
<ul>
<li> <a href='%(baseurl)s/login'>Login</a>: Basic Authentication for a name and password.
<li> <a href='%(baseurl)s/crash'>Crash</a>: Force a server crash.
<li> <a href='%(baseurl)s/debug'>Debug</a>: Output debug information; CGI info.
<li> <a href='%(baseurl)s/doc'>Doc</a>: Produce documentation of the API for
     this web resource by introspection.
</ul>
<p>wrapid is a different web server framework with some novel features:
<ul>
<li> Designed to facilitate web resource implementation.
<li> Allows the creation of a well-organized RESTful API that is uniform
     for all representations, including HTML for human browsers, or JSON
     and other content types for programmatic access.
<li> Separates the retrieval/operation on server-side data from the creation
     of a specific response representation.
<li> Built-in support to produce documentation of the API by introspection.
<li> Agnostic as to back-end storage; no ORM, or other built-in DB connection.
<li> Written in Python 2.6 using WSGI as the web server interface.
</ul>
</p>

<p>
The code for wrapid lives at <a href="%(github)s">github (user pekrau)</a>.
</p>
<p>
This site can also be viewed at <a href="%(scilifelab)s">SciLifeLab</a>.
</p>
</body>
</html>
""" % lookup)
    return response
root.mimetype = 'text/html'

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
    raise ValueError('blah')

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


application = Application(name='wrapid example',
                          version=__version__,
                          debug=True)

application.append(Resource('/', name='Root', GET=root))
application.append(Resource('/login', name='Login', GET=login))
application.append(Resource('/crash', name='Crash', GET=crash))
application.append(Resource('/debug', name='Debug', GET=debug))

static_dirpath = os.path.join(os.path.dirname(__file__), 'static')
application.append(Resource('/static/{filename}', name='Static file',
                            GET=GET_Static(static_dirpath)))

application.append(Resource('/factory', name='Factory',
                            POST=POST(infields=Fields(
                                TextField('thing',
                                          required=True,
                                          descr='Thing to make.'))),
                            descr='Dummy to show POST method documentation.'))

application.append(Resource('/doc', name='Documentation',
                            GET=GET_Documentation(),
                            descr='Produce documentation of the API for'
                            ' this web resource by introspection.'))
