""" wrapid: Web Resource API server framework built on Python WSGI.

Access to files in a predetermined directory on the server.
"""

import os.path
import mimetypes
import time

from .methods import *
from .utils import DATETIME_WEB_FORMAT


class GET_File(GET):
    """Return the specified file from a predefined server directory.
    The mimetype of the response is determined by the file name extension.
    """

    # To be modified in an inheriting class.
    dirpath        = None
    chunk_size     = 2**20
    check_modified = True
    cache_control  = None

    # Add missing mimetypes, or override those in mimetypes module
    MIMETYPES = dict(json='application/json')

    def prepare(self, request):
        self.headers = wsgiref.headers.Headers([])
        # Default dirpath, in case class variable is not redefined
        if not self.dirpath:
            self.dirpath = os.path.join(os.path.dirname(__file__), 'static')
        filename = request.variables['filename']
        format = request.variables.get('FORMAT')
        if format:
            filename += format
        filename = filename.lstrip('./~') # Remove dangerous characters.
        self.filepath = os.path.join(self.dirpath, filename)
        if not os.path.exists(self.filepath):
            raise HTTP_NOT_FOUND
        if not os.path.isfile(self.filepath):
            raise HTTP_NOT_FOUND
        mtime = os.path.getmtime(self.filepath)
        mod_file = time.strftime(DATETIME_WEB_FORMAT, time.gmtime(mtime))
        if self.check_modified:
            mod_since = request.headers['If-Modified-Since']
            if mod_since == mod_file:   # Don't bother comparing '<'.
                raise HTTP_NOT_MODIFIED
            else:
                self.headers.add_header('Last-Modified', mod_file)
        if self.cache_control:
            self.headers.add_header('Cache-Control', self.cache_control)
        try:
            ext = os.path.splitext(self.filepath)[-1].lstrip('.')
            mimetype = self.MIMETYPES[ext]
        except KeyError:
            mimetype = mimetypes.guess_type(self.filepath)[0]
            if not mimetype:
                mimetype = 'application/octet-stream'
        self.headers.add_header('Content-Type', mimetype)

    def get_response(self, request):
        response = HTTP_OK_Static(**dict(self.headers))
        try:
            response.open(self.filepath, chunk_size=self.chunk_size)
        except IOError, msg:
            raise HTTP_NOT_FOUND
        return response


class HTTP_OK_Static(HTTP_OK):
    "Return the contents of a static file in chunks."

    def open(self, filepath, chunk_size=2**20):
        self.file = open(filepath)
        self.chunk_size = chunk_size

    def __iter__(self):
        return self

    def next(self):
        chunk = self.file.read(self.chunk_size)
        if not chunk:
            self.file.close()
            raise StopIteration
        return chunk
