""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Unit test framework for accessing wrapid-style web resources.
"""

import unittest
import optparse
import wsgiref.headers
import json

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
