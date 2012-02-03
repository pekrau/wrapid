""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Interface to a web resource, using JSON as default representation format.
"""

import urlparse
import httplib
import urllib
import base64
import wsgiref.headers
import json
import copy


class Webresource(object):
    "Interface to a web resource."

    def __init__(self, url, account=None, password=None):
        assert url
        self.set_url(url)
        self.account = account
        self.password = password
        self.accept = 'application/json'

    def __str__(self):
        return self.url

    def set_url(self, url):
        parts = urlparse.urlparse(url)
        self.scheme = parts.scheme
        if not self.scheme in ['http', 'https']:
            raise ValueError('url scheme must be http or https')
        self.host = parts.netloc.split(':')[0]
        self.port = parts.port
        self.root = parts.path.rstrip('/') + '/'

    def get_url(self):
        if self.port:
            netloc = "%s:%s" % (self.host, self.port)
        else:
            netloc = self.host
        return urlparse.urlunsplit((self.scheme, netloc, self.root, '', ''))

    url = property(get_url, set_url)

    def request(self, method, path, body=None, headers=dict()):
        """Send the request using the specified HTTP method.
        The response is an instance of httplib.HTTPResponse,
        which has the following attributes:
          status        HTTP status code
          reason        HTTP status phrase
          msg           a mimetools.Message instance containing headers
          read()        returns the response body
          getheader(name, [default])  returns the specified header
          getheaders()  returns the headers as tuples
        """
        cnx = httplib.HTTPConnection(self.host, self.port)
        cnx.request(method, path, body=body, headers=headers)
        return cnx.getresponse()

    def get_path(self, rpath):
        "Get the full URL path from the resource path relative to root."
        return self.root + rpath.lstrip('/')

    def get_rpath(self, url):
        """Return the resource path relative to root from the full URL.
        Raises ValueError if the URL does not refer to this web resource.
        """
        parts = urlparse.urlparse(url)
        if not parts.scheme in ['http', 'https']:
            raise ValueError('url scheme must be http or https')
        if self.host != parts.netloc.split(':')[0]:
            raise ValueError('netloc of URL does not match')
        if self.port != parts.port:
            raise ValueError('port of URL does not match')
        if not parts.path.startswith(self.root):
            raise ValueError('path root of URL does not match')
        return '/' + parts.path[len(self.root):]

    def get_headers(self, **headers):
        headers = wsgiref.headers.Headers([(k.replace('_', '-'), v)
                                           for k,v in headers.items()
                                           if v])
        if not headers['accept']:
            headers.add_header('Accept', self.accept)
        if self.account and self.password:
            encoded = base64.b64encode("%s:%s" % (self.account, self.password))
            headers.add_header('Authorization', "Basic %s" % encoded)
        return dict(headers.items())

    def copy(self):
        return copy.copy(self)

    def GET(self, rpath, **query):
        """Retrieve the representation of the given resource,
        which is specified relative to the root URL.
        """
        path = self.get_path(rpath)
        if query:
            path += '?' + urllib.urlencode(query)
        return self.request('GET', path, headers=self.get_headers())

    def POST(self, rpath, data=None, content_type='application/json'):
        """Post the data, if any.
        If the content type is 'application/json', then encode it as such.
        Else assume that it has already been encoded, and send as is.
        """
        if data:
            if content_type == 'application/json':
                body = json.dumps(data)
            else:
                body = data
            headers = self.get_headers(content_type=content_type)
        else:
            body = None
            headers = self.get_headers()
        path = self.get_path(rpath)
        return self.request('POST', path, body, headers)

    def PUT(self, rpath, data=None, content_type='application/json'):
        """Put the data, if any.
        If the content type is 'application/json', then encode it as such.
        Else assume that it has already been encoded, and send as is.
        """
        if data:
            if content_type == 'application/json':
                body = json.dumps(data)
            else:
                body = data
            headers = self.get_headers(content_type=content_type)
        else:
            body = None
            headers = self.get_headers()
        path = self.get_path(rpath)
        return self.request('PUT', path, body, headers)

    def DELETE(self, rpath):
        "Delete the specified resource."
        path = self.get_path(rpath)
        return self.request('DELETE', path, headers=self.get_headers())


if __name__ == '__main__':
    wr = Webresource('http://localhost/wrapid')
    print wr, id(wr), wr.accept
    wr2 = wr.copy()
    wr2.accept = 'text/plain'
    print wr2, id(wr2), wr2.accept
    print wr, id(wr), wr.accept
    response = wr.GET('/doc')
    print response.status, response.reason, len(response.read())
    response = wr.POST('/factory')
    print response.status, response.reason, response.read()
