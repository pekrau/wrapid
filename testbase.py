""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Unit test framework for accessing wrapid-style web resources.
"""

import unittest
import optparse
import httplib
import urllib
import urlparse
import wsgiref.headers
import base64
import json


class TestBase(unittest.TestCase):
    "Base test class providing a set of standard methods."

    def get_connection(self):
        "Get a connection instance for one request-response interaction."
        try:
            host, port = self.configuration.netloc.split(':', 1)
        except ValueError:
            host = self.configuration.netloc
            port = None
        return httplib.HTTPConnection(host, port)

    def get_path(self, path_or_url):
        "Return the resource path given a full path or URL."
        parts = urlparse.urlparse(path_or_url)
        if parts.scheme:
            self.assertEqual(parts.scheme, 'http')
            self.assertEqual(parts.netloc, self.configuration.netloc)
        if parts.path.startswith(self.configuration.root):
            return parts.path[len(self.configuration.root):]
        else:
            return parts.path

    def get_urlpath(self, resource, **query):
        "Return the full URL path given the resource path."
        path = self.configuration.root.rstrip('/') + '/' + resource.lstrip('/')
        if query:
            path += '?' + urllib.urlencode(query)
        return path

    def get_headers(self, **hdrs):
        "Return a dictionary of HTTP headers."
        headers = wsgiref.headers.Headers([(k.replace('_', '-'), v)
                                           for k,v in hdrs.items()])
        encoded = base64.b64encode("%s:%s" % (self.configuration.account,
                                              self.configuration.password))
        headers.add_header('Authorization', "Basic %s" % encoded)
        return dict(headers.items())

    def get_json_data(self, response):
        try:
            return json.loads(response.read())
        except ValueError, msg:
            self.fail(msg)

    def GET(self, resource, accept='application/json', **query):
        cnx = self.get_connection()
        cnx.request('GET', self.get_urlpath(resource, **query),
                    headers=self.get_headers(accept=accept))
        return cnx.getresponse()

    def POST(self, resource, accept='application/json', outdata=None):
        cnx = self.get_connection()
        if outdata:
            body = json.dumps(outdata)
            headers = self.get_headers(accept=accept,
                                       content_type='application/json')
        else:
            body = None
            headers = self.get_headers(accept=accept)
        cnx.request('POST', self.get_urlpath(resource),
                    body=body,
                    headers=headers)
        return cnx.getresponse()

    def DELETE(self, resource):
        cnx = self.get_connection()
        cnx.request('DELETE', self.get_urlpath(resource),
                    headers=self.get_headers())
        return cnx.getresponse()


class TestExecutor(object):
    "Execute the tests in a set of TestCase classes."

    def __init__(self, netloc='localhost', root='/',
                 account='test', password='abc123', verbosity=2):
        self.netloc = netloc
        self.root = root
        self.account = account
        self.password = password
        self.verbosity = verbosity
        self.parse_command_line()

    def parse_command_line(self):
        parser = optparse.OptionParser()
        parser.add_option('--account', '-a',
                          action='store',
                          default=self.account)
        parser.add_option('--password', '-p', action='store')
        url = urlparse.urlunsplit(('http', self.netloc, self.root, '', ''))
        parser.add_option('--url', '-u', action='store', default=url)
        parser.add_option('--verbosity', '-v', action='store', type='int',
                          default=self.verbosity)
        options, arguments = parser.parse_args()
        if options.url:
            parts = urlparse.urlsplit(options.url)
            if parts.scheme != 'http':
                raise ValueError("no support for '%s' scheme" % parts.scheme)
            self.netloc = parts.netloc
            self.root = parts.path
        self.account = options.account
        if options.password:
            self.password = options.password
        self.verbosity = options.verbosity

    def test(self, *klasses):
        suites = []
        for klass in klasses:
            klass.configuration = self
            suites.append(unittest.TestLoader().loadTestsFromTestCase(klass))
        alltests = unittest.TestSuite(suites)
        unittest.TextTestRunner(verbosity=self.verbosity).run(alltests)
