""" wrapid: Web Resource API server framework built on Python WSGI.

Text representation of data using Python 'pprint'.
"""

import pprint

from .representation import *


class TextRepresentation(Representation):
    "Text representation of the resource using Python 'pprint'."

    mimetype = 'text/plain'
    format = 'txt'

    def __call__(self, data):
        response = HTTP_OK(**self.get_http_headers())
        response.append(pprint.pprint(data, indent=2))
        return response
