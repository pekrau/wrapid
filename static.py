""" wrapid: Web Resource API server framework built on Python WSGI.

Access to static files in a predetermined directory on the server.
"""

import logging

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

    def __init__(self, dirpath, cache_control=None, chunk_size=2**20,
                 check_modified=True, descr=None):
        assert chunk_size > 0
        super(GET_Static, self).__init__(descr=descr)
        self.dirpath = dirpath
        self.cache_control = cache_control
        self.chunk_size = chunk_size
        self.check_modified = check_modified

    def prepare(self, resource, request, application):
        self.headers = wsgiref.headers.Headers([])
        filename = resource.variables['filename']
        format = resource.variables.get('FORMAT')
        if format:
            filename += format
        filename = filename.lstrip('./~') # Remove dangerous characters.
        self.filepath = os.path.join(self.dirpath, filename)
        if not os.path.exists(self.filepath):
            logging.debug("static not exists '%s'", self.filepath)
            raise HTTP_NOT_FOUND
        if not os.path.isfile(self.filepath):
            logging.debug("static not file '%s'", self.filepath)
            raise HTTP_NOT_FOUND
        mtime = os.path.getmtime(self.filepath)
        mod_file = time.strftime(DATETIME_WEB_FORMAT, time.gmtime(mtime))
        self.headers.add_header('Last-Modified', mod_file)
        if self.check_modified:
            mod_since = request.headers['If-Modified-Since']
            if mod_since == mod_file:   # Don't bother comparing '<'.
                raise HTTP_NOT_MODIFIED
        try:
            ext = os.path.splitext(self.filepath)[-1].lstrip('.')
            mimetype = self.MIMETYPES[ext]
        except KeyError:
            mimetype = mimetypes.guess_type(self.filepath)[0]
            if not mimetype:
                mimetype = 'application/octet-stream'
        self.headers.add_header('Content-Type', mimetype)
        if self.cache_control:
            self.headers.add_header('Cache-Control', self.cache_control)

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
