""" wrapid: Micro framework built on Python WSGI for RESTful server APIs

JSON representation.
"""

import json

from .representation import *


class JsonRepresentation(Representation):
    "JSON representation of the resource."

    mimetype = 'application/json'
    charset = 'utf-8'
    format = 'json'
    indent = 2

    def __call__(self, data):
        response = HTTP_OK(**self.get_http_headers())
        response.append(json.dumps(data, indent=self.indent))
        return response
