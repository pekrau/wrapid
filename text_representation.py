""" wrapid: Micro framework built on Python WSGI for RESTful server APIs

Text representation using Python 'pprint'.
"""

import pprint

from .representation import *
from .utils import rstr


class TextRepresentation(Representation):
    "Text representation of the resource using Python 'pprint'."

    mimetype = 'text/plain'
    charset = 'utf-8'
    format = 'txt'

    def __call__(self, data):
        response = HTTP_OK(**self.get_http_headers())
        response.append(pprint.pformat(rstr(data), indent=2))
        return response
