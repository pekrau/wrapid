""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Base unit test class for the web resource API.
"""

import unittest
import optparse
import httplib
import wsgiref.headers
import base64
import json
import urllib
import urlparse
import time


class BaseTest(unittest.TestCase):
    "Base unit test class with utility methods for HTTP operations."

    # The setup dictionary must be defined in the inheriting class.
    SETUP = dict(NETLOC = None,
                 ROOT = None,
                 ACCOUNT = None,
                 PASSWORD = None)

    def get_connection(self):
        try:
            host, port = self.SETUP['NETLOC'].split(':', 1)
        except ValueError:
            host = self.SETUP['NETLOC']
            port = None
        return httplib.HTTPConnection(host, port)

    def get_path(self, path_or_url):
        parts = urlparse.urlparse(path_or_url)
        if parts.scheme:
            self.assertEqual(parts.scheme, 'http')
            self.assertEqual(parts.netloc, self.SETUP['NETLOC'])
        if parts.path.startswith(self.SETUP['ROOT']):
            return parts.path[len(self.SETUP['ROOT']):]
        else:
            return parts.path

    def get_headers(self, accept='application/json', **hdrs):
        headers = wsgiref.headers.Headers([(k.replace('_', '-'), v)
                                           for k,v in hdrs.items()])
        encoded = base64.b64encode("%s:%s" % (self.SETUP['ACCOUNT'],
                                              self.SETUP['PASSWORD']))
        auth = "Basic %s" % encoded
        headers.add_header('Authorization', auth)
        headers.add_header('Accept', accept)
        return dict(headers.items())

    def GET(self, resource, accept='application/json', **query):
        cnx = self.get_connection()
        urlpath = self.SETUP['ROOT'] + resource
        if query:
            urlpath += '?' + urllib.urlencode(query)
        cnx.request('GET', urlpath, headers=self.get_headers(accept=accept))
        return cnx.getresponse()

    def POST(self, resource, accept='application/json', outdata=None):
        cnx = self.get_connection()
        urlpath = self.SETUP['ROOT'] + resource
        if outdata:
            cnx.request('POST', urlpath,
                        body=json.dumps(outdata),
                        headers=self.get_headers(accept=accept,
                                                 content_type='application/json'))
        else:
            cnx.request('POST', urlpath,
                        headers=self.get_headers(accept=accept))
        return cnx.getresponse()

    def DELETE(self, resource):
        cnx = self.get_connection()
        urlpath = self.SETUP['ROOT'] + resource
        cnx.request('DELETE', urlpath, headers=self.get_headers())
        return cnx.getresponse()


def get_setup(defaults=dict()):
    "Return the setup dictionary from the command line or the defaults."
    parser = optparse.OptionParser()
    parser.add_option('--account', '-a', action='store',
                      default=defaults['ACCOUNT'])
    parser.add_option('--password', '-p', action='store')
    url = urlparse.urlunsplit(('http',
                               defaults['NETLOC'],
                               defaults['ROOT'],
                               '',
                               ''))
    parser.add_option('--url', '-u', action='store', default=url)
    options, arguments = parser.parse_args()
    result = defaults.copy()
    if options.url:
        parts = urlparse.urlsplit(options.url)
        if parts.scheme != 'http':
            raise ValueError("no support for '%s' scheme" % parts.scheme)
        result['NETLOC'] = parts.netloc
        result['ROOT'] = parts.path
    if options.account:
        result['ACCOUNT'] = options.account
    if options.password:
        result['PASSWORD'] = options.password
    return result


def run_tests(setup, *classes):
    suites = []
    for klass in classes:
        klass.SETUP = setup
        suites.append(unittest.TestLoader().loadTestsFromTestCase(klass))
    alltests = unittest.TestSuite(suites)
    unittest.TextTestRunner(verbosity=2).run(alltests)
