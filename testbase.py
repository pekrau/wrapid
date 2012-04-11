""" wrapid: Web Resource API server framework built on Python WSGI.

Unit test framework for accessing wrapid-style web resources.
"""

import unittest
import optparse
import httplib
import wsgiref.headers
import json
from xml.etree import ElementTree

from wrapid.webresource import Webresource


class TestBase(unittest.TestCase):
    "Base test class providing a set of standard methods."

    def get_wr(self, accept):
        "Get a copy of the Webresource instance with another Accept type."
        wr = self.wr.copy()
        wr.accept = accept
        return wr

    def get_headers(self, response):
        return wsgiref.headers.Headers(response.getheaders())

    def get_json_data(self, response):
        try:
            return json.loads(response.read())
        except ValueError:
            self.fail('invalid JSON data')

    def get_txt_data(self, response):
        try:
            return eval(response.read())
        except Exception:
            self.fail('invalid TXT pprint data')

    def get_xml_data(self, response):
        try:
            return ElementTree.fromstring(response.read())
        except ValueError:
            self.fail('invalid XML data')


class TestExecutor(object):
    "Execute the tests in a set of TestCase classes."

    def __init__(self, url='http://localhost/',
                 account='test', password='abc123', verbosity=2):
        self.wr = Webresource(url, account=account, password=password)
        self.verbosity = verbosity
        self.parse_command_line()

    def parse_command_line(self):
        parser = optparse.OptionParser()
        parser.add_option('--account', '-a',
                          action='store',
                          default=self.wr.account)
        parser.add_option('--password', '-p', action='store')
        parser.add_option('--url', '-u', action='store', default=self.wr.url)
        parser.add_option('--verbosity', '-v', action='store', type='int',
                          default=self.verbosity)
        options, arguments = parser.parse_args()
        if options.url:
            self.wr.url = options.url
        self.wr.account = options.account
        if options.password:
            self.wr.password = options.password
        self.verbosity = options.verbosity

    def test(self, *klasses):
        suites = []
        for klass in klasses:
            klass.wr = self.wr
            suites.append(unittest.TestLoader().loadTestsFromTestCase(klass))
        alltests = unittest.TestSuite(suites)
        unittest.TextTestRunner(verbosity=self.verbosity).run(alltests)


class TestAccess(TestBase):
    "Test basic access to a standard web application."

    def test_GET_home_HTML(self):
        "Fetch the home page, in HTML format."
        wr = self.get_wr('text/html')
        response = wr.GET('/')
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        headers = self.get_headers(response)
        self.assert_(headers.get('content-type').startswith('text/html'))

    def test_GET_home_JSON(self):
        "Fetch the home page, in JSON format."
        response = self.wr.GET('/')
        self.assertEqual(response.status, httplib.OK,
                         msg="HTTP status %s" % response.status)
        headers = self.get_headers(response)
        self.assert_(headers['content-type'].startswith('application/json'),
                     msg=headers['content-type'])
        self.get_json_data(response)

    def test_GET_home_XYZ(self):
        "Try fetching the home page in an non-existent format."
        wr = self.get_wr('text/xyz')
        response = wr.GET('/')
        self.assertEqual(response.status, httplib.NOT_ACCEPTABLE,
                         msg="HTTP status %s" % response.status)

    def test_GET_nonexistent(self):
        "Try fetching a non-existent resource."
        response = self.wr.GET('/doesnotexist')
        self.assertEqual(response.status, httplib.NOT_FOUND,
                         msg="HTTP status %s" % response.status)


if __name__ == '__main__':
    URL = 'http://localhost/wrapid'
    ex = TestExecutor(url=URL)
    print 'Testing', ex.wr
    ex.test(TestAccess)
