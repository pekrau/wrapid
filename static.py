""" wrapid: Web Resource API server framework built on Python WSGI.

Access to static files in a predetermined directory on the server.
"""

import os.path
import mimetypes
import time

from .resource import *
from .utils import DATETIME_WEB_FORMAT


class GET_Static(GET):
    """Return the specified static file from a predefined server directory.
    The mimetype of the response is determined by the file name extension.
    """

    # Add missing mimetypes, or override those in mimetypes module
    MIMETYPES = dict(json='application/json')

    def __init__(self, dirpath,
                 cache_control=None, chunk_size=2**20, descr=None):
        assert chunk_size > 0
        super(GET_Static, self).__init__(descr=descr)
        self.dirpath = dirpath
        self.cache_control = cache_control
        self.chunk_size = chunk_size

    def prepare(self, resource, request, application):
        filename = resource.variables['filename']
        format = resource.variables.get('FORMAT')
        if format:
            filename += format
        filename = os.path.basename(filename) # Security
        self.filepath = os.path.join(self.dirpath, filename)
        if not os.path.exists(self.filepath):
            raise HTTP_NOT_FOUND
        if not os.path.isfile(self.filepath):
            raise HTTP_NOT_FOUND
        mtime = os.path.getmtime(self.filepath)
        mod_file = time.strftime(DATETIME_WEB_FORMAT, time.gmtime(mtime))
        mod_since = request.headers['If-Modified-Since']
        if mod_since == mod_file:       # Don't bother comparing '<'.
            raise HTTP_NOT_MODIFIED
        try:
            ext = os.path.splitext(self.filepath)[1].lstrip('.')
            mimetype = self.MIMETYPES[ext]
        except KeyError:
            mimetype = mimetypes.guess_type(self.filepath)[0]
            if not mimetype:
                mimetype = 'application/octet-stream'
        self.headers = wsgiref.headers.Headers([('Content-Type', mimetype)])
        if self.cache_control:
            self.headers.add_header('Cache-Control', self.cache_control)
        self.headers.add_header('Last-Modified', mod_file)

    def get_response(self, resource, request, application):
        response = HTTP_OK_Static(**dict(self.headers))
        response.chunk_size = self.chunk_size
        try:
            response.open(self.filepath)
        except IOError, msg:
            raise HTTP_NOT_FOUND
        return response


class HTTP_OK_Static(HTTP_OK):
    "Return the contents of a static file in chunks."

    chunk_size = 2**20                  # 1,048,576

    def open(self, filepath):
        self.file = open(filepath)

    def __iter__(self):
        return self

    def next(self):
        chunk = self.file.read(self.chunk_size)
        if not chunk:
            self.file.close()
            raise StopIteration
        return chunk
