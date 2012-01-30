""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

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

    # Missing mimetypes, or overrides over those in mimetypes module
    MIMETYPES = dict(json='application/json')

    def __init__(self, dirpath, cache_control=None, descr=None):
        super(GET_Static, self).__init__(descr=descr)
        self.dirpath = dirpath
        self.cache_control = cache_control

    def __call__(self, resource, request, application):
        filename = resource.variables['filename']
        format = resource.variables.get('FORMAT')
        if format:
            filename += format
        filename = os.path.basename(filename) # Security
        filepath = os.path.join(self.dirpath, filename)
        if not os.path.exists(filepath):
            raise HTTP_NOT_FOUND
        if not os.path.isfile(filepath):
            raise HTTP_NOT_FOUND
        mtime = os.path.getmtime(filepath)
        mod_file = time.strftime(DATETIME_WEB_FORMAT, time.gmtime(mtime))
        mod_since = request.headers['If-Modified-Since']
        if mod_since == mod_file:       # Don't bother comparing '<'.
            logging.debug("HTTP Not Modified")
            raise HTTP_NOT_MODIFIED
        try:
            ext = os.path.splitext(filepath)[1].lstrip('.')
            mimetype = self.MIMETYPES[ext]
        except KeyError:
            mimetype = mimetypes.guess_type(filepath)[0]
            if not mimetype:
                mimetype = 'application/octet-stream'
        headers = wsgiref.headers.Headers([('Content-Type', mimetype)])
        if self.cache_control:
            headers.add_header('Cache-Control', self.cache_control)
        headers.add_header('Last-Modified', mod_file)
        response = HTTP_OK(**dict(headers))
        try:
            infile = open(filepath)
        except IOError, msg:
            logging.error("wrapid: static file not found: %s", msg)
            raise HTTP_NOT_FOUND
        else:
            response.append(infile.read())
            infile.close()
        return response
