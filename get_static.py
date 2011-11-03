""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Access to static files in a predetermined directory on the server.
"""

import logging
import os.path
import mimetypes

from .resource import *


class GET_Static(Method):
    """Return the specified static file. The mimetype of the response
    is determined by the extension of the file name.
    """

    # Missing mimetypes, or overrides over those in mimetypes module
    MIMETYPES = dict(json='application/json')

    def __init__(self, dirpath, cache_control=None, descr=None):
        super(GET_Static, self).__init__(descr=descr)
        self.dirpath = dirpath
        self.cache_control = cache_control
        self.outreprs = [DummyRepresentation('*/*',
                                             'The mimetype is inferred from'
                                             ' the file name extension.')]

    def __call__(self, resource, request, application):
        filename = resource.variables['filename']
        format = resource.variables.get('FORMAT')
        if format:
            filename += format
        filename = os.path.basename(filename) # Security
        filename = os.path.join(self.dirpath, filename)
        try:
            ext = os.path.splitext(filename)[1].lstrip('.')
            mimetype = self.MIMETYPES[ext]
        except KeyError:
            mimetype = mimetypes.guess_type(filename)[0]
            if not mimetype:
                mimetype = 'application/octet-stream'
        headers = wsgiref.headers.Headers([('Content-Type', mimetype)])
        if self.cache_control:
            headers.add_header('Cache-Control', self.cache_control)
        response = HTTP_OK(**dict(headers))
        try:
            infile = open(filename)
        except IOError, msg:
            logging.error("wrapid: static not found: %s", msg)
            raise HTTP_NOT_FOUND
        else:
            response.append(infile.read())
            infile.close()
        return response
