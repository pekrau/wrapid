""" wrapid: Micro framework built on Python WSGI for RESTful server APIs

Access to files in a predetermined directory on the server.
"""

import os.path
import mimetypes
import time

from .methods import *
from .utils import DATETIME_WEB_FORMAT


class File(GET):
    """Return the specified file from a predefined server directory.
    The mimetype of the response is determined by the file name extension.
    """

    # To be modified in an inheriting class.
    dirpath        = None
    chunk_size     = 2**20
    check_modified = True
    cache_control  = None
    charset        = None
    as_attachment  = False              # True: named file download

    # Add missing mimetypes, or override those in mimetypes module
    MIMETYPES = dict(json='application/json')

    def prepare(self, request):
        self.headers = wsgiref.headers.Headers([])
        if not self.dirpath:
            self.dirpath = self.get_dirpath(request)
        self.filepath = self.get_filepath(request)
        self.fullpath = os.path.join(self.dirpath, self.filepath)
        self.fullpath = os.path.normpath(self.fullpath)
        # Security: disallow navigating outside of directory
        if not self.fullpath.startswith(os.path.normpath(self.dirpath)):
            raise HTTP_NOT_FOUND
        if not os.path.exists(self.fullpath):
            raise HTTP_NOT_FOUND
        if not os.path.isfile(self.fullpath):
            raise HTTP_NOT_FOUND
        mtime = os.path.getmtime(self.fullpath)
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
            ext = os.path.splitext(self.fullpath)[-1].lstrip('.')
            contenttype = self.MIMETYPES[ext]
        except KeyError:
            contenttype = mimetypes.guess_type(self.fullpath)[0]
            if not contenttype:
                contenttype = 'application/octet-stream'
        charset = self.get_charset(request)
        if charset:
            contenttype += "; charset=%s" % charset
        self.headers.add_header('Content-Type', contenttype)
        if self.as_attachment:
            filename = os.path.split(self.filepath)[1]
            self.headers.add_header('Content-Disposition',
                                    'attachment; filename="%s"' % filename)

    def get_dirpath(self, request):
        "Get directory path, if not already defined at class level."
        raise NotImplementedError

    def get_filepath(self, request):
        "Return the specified file path; will be concatenated with dirpath."
        filepath = request.variables['filepath']
        format = request.variables.get('FORMAT')
        if format:
            filepath += format
        return filepath

    def get_charset(self, request):
        "Return the character encoding, if any."
        return self.charset

    def get_response(self, request):
        response = HTTP_OK_Static(**dict(self.headers))
        try:
            response.open(self.fullpath, chunk_size=self.chunk_size)
        except IOError, msg:
            raise HTTP_NOT_FOUND
        return response


class HTTP_OK_Static(HTTP_OK):
    "Return the contents of a static file in chunks."

    def open(self, fullpath, chunk_size=2**20):
        self.file = open(fullpath)
        self.chunk_size = chunk_size

    def __iter__(self):
        return self

    def next(self):
        chunk = self.file.read(self.chunk_size)
        if not chunk:
            self.file.close()
            raise StopIteration
        return chunk
