""" wrapid: Web Resource API server framework built on Python WSGI.

Text representation using Python 'pprint'.
"""

import pprint

from .representation import *


class TextRepresentation(Representation):
    "Text representation of the resource using Python 'pprint'."

    mimetype = 'text/plain'
    charset = 'utf-8'
    format = 'txt'

    def __call__(self, data):
        response = HTTP_OK(**self.get_http_headers())
        response.append(pprint.pformat(data, indent=2))
        return response
