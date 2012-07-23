""" wrapid: Micro framework built on Python WSGI for RESTful server APIs

Base class for standard XML representation using ElementTree.
"""

import xml.etree.ElementTree

from wrapid.representation import *


class XmlRepresentation(Representation):
    "XML representation of the resource using ElementTree.TreeBuilder."

    mimetype = 'application/xml'
    charset = 'utf-8'
    format = 'xml'

    def __call__(self, data):
        response = HTTP_OK(**self.get_http_headers())
        element = self.data_to_element(data)
        response.append('<?xml version="1.0" encoding="%s"?>' % self.charset)
        response.append(xml.etree.ElementTree.tostring(element, self.charset))
        return response

    def data_to_element(self, data):
        "Return an ElementTree element produced from the data dictionary."
        self.builder = xml.etree.ElementTree.TreeBuilder()
        self.builder.start('data', dict())
        self.item_to_element(data)
        self.builder.end('data')
        return self.builder.close()

    def item_to_element(self, item):
        "Recursively build elements from the given data item."
        if isinstance(item, dict):
            for name in sorted(item.keys()):
                self.builder.start(name, dict())
                self.item_to_element(item[name])
                self.builder.end(name)
        elif isinstance(item, (tuple, list)):
            for part in item:
                self.builder.start('item', dict())
                self.item_to_element(part)
                self.builder.end('item')
        else:
            self.builder.data(unicode(item))
