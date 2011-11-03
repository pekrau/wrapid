""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

JSON representation of data.
"""

import json

from .resource import *


class JsonRepresentation(Representation):
    "JSON representation of the resource."

    mimetype = 'application/json'
    format = 'json'

    def __call__(self, data):
        self.modify(data)
        response = HTTP_OK(**self.get_http_headers())
        response.append(json.dumps(data, indent=2))
        return response

    def modify(self, data):
        "Modify the data before output."
        pass
