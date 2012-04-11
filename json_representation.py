""" wrapid: Web Resource API server framework built on Python WSGI.

JSON representation of data.
"""

import json

from .representation import *


class JsonRepresentation(Representation):
    "JSON representation of the resource."

    mimetype = 'application/json'
    charset = 'utf-8'
    format = 'json'

    def __call__(self, data):
        response = HTTP_OK(**self.get_http_headers())
        response.append(json.dumps(data, indent=2))
        return response
