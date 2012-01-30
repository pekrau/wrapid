""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Produce the documentation for this web application by introspection.
"""

import logging
import json
import pprint
import urlparse

from HyperText.HTML40 import *

from .fields import *
from .utils import HTTP_METHODS
from .response import *
from .resource import (Representation, GET, FieldsMethodMixin,
                       InreprsMethodMixin, OutreprsMethodMixin)
from .json_representation import JsonRepresentation
from .text_representation import TextRepresentation


class HtmlRepresentation(Representation):
    "HTML representation suitable for display in a browser."

    mimetype = 'text/html'
    format = 'html'
    css_href = None
    css_class = 'wrapid-doc'

    def __call__(self, data):
        title = data['documentation']['application']
        try:
            title += ' ' + data['documentation']['version']
        except KeyError:
            pass
        items = [TITLE(title),
                 META(content='text/html; charset=utf-8',
                      http_equiv='Content-Type')]
        if self.css_href:
            if urlparse.urlsplit(self.css_href)[1]: # Absolute URL
                css_href = self.css_href
            else:                                   # Relative URL; to absolute
                base = data['documentation']['href'].rstrip('/') + '/'
                relative = self.css_href.lstrip('/')
                css_href = urlparse.urljoin(base, relative)
            items.append(LINK(rel='stylesheet', href=css_href, type='text/css'))
        else:
            items.append(STYLE("""
<!--
.wrapid-doc {font-family: Arial, Helvetica, sans-serif;
	     font-size: small; }
h1.wrapid-doc {font-size: x-large;
               margin-left: 3em; }
h2.wrapid-doc {font-size: large;
               margin-left: 2em; }
h3.wrapid-doc {font-size: small;
               margin-left: 1em; }
h4.wrapid-doc {font-size: small;
               margin-left: 0em; }
table.wrapid-doc {margin-top: 0.5em;
		  margin-bottom: 0.5em; }
table.wrapid-doc caption {padding-left: 2em;
			  margin-bottom: 0.25em;
			  text-align: left;
			  font-weight: bold; }
table.wrapid-doc tr th {border-width: 2px;
			border-top-style: solid;
			border-bottom-style: solid;
			padding-left: 0.5em;
                        text-align: left; }
table.wrapid-doc tr td {border-width: 1px;
			border-bottom-style: solid;
			padding-left: 0.5em; }
-->
""",
                               type='text/css'))
        head = HEAD(*items)

        elems = [H1(title, klass=self.css_class),
                 P('This document describes the application programming'
                   ' interface (API) for this web resource. It is produced'
                   ' automatically by a procedure that performs introspection'
                   ' on the Python source code of the application.',
                   klass=self.css_class),
                 P('The fundamental idea is that the set of URLs defining the'
                   ' API is identical to the URLs used by the human user'
                   ' agents (browsers). This reduces complexity and increases'
                   ' clarity. The only difference is that browsers request HTML'
                   ' representations, while the JSON representation is intended'
                   ' for programmatic user agents. The representations contain'
                   ' the same logical data, including the description of links,'
                   ' forms and representations.',
                   klass=self.css_class)]
        others = [A("%(title)s (%(mimetype)s)" % r, href=r['href'])
                  for r in data['outreprs'] if r['mimetype'] != 'text/html']
        others = map(str, others)
        elems.append(P("This resource in other formats: %s." %', '.join(others),
                       klass=self.css_class))
        elems.append(H2(data['documentation']['href'], klass=self.css_class))
        rows = [TR(TH('Resource'),
                   TH('URL'),
                   TH('Description'))]
        for resource in data['resources']:
            rows.append(TR(TD(A(resource['resource'],
                                href="#%(resource)s: %(href)s" % resource)),
                           TD(resource['href']),
                           TD(resource.get('descr'))))
        elems.append(TABLE(klass=self.css_class, *rows))
        for resource in data['resources']:
            title = "%(resource)s: %(href)s" % resource
            elems.append(H2(A(title, id=title), klass=self.css_class))
            elems.append(P(resource['descr'], klass=self.css_class))
            for name in HTTP_METHODS:
                try:
                    method = resource['methods'][name]
                except KeyError:
                    continue
                elems.append(H3(name, klass=self.css_class))
                elems.append(P(method['descr'], klass=self.css_class))

                rows = [CAPTION('Input fields'),
                        TR(TH('Parameter'),
                           TH('Required'),
                           TH('Type'),
                           TH('Options'),
                           TH('Default'),
                           TH('Description'))]
                fields = method.get('fields', [])
                for field in fields:
                    try:
                        options = field['options']
                        if not options: raise KeyError
                    except KeyError:
                        options = '-'
                    else:
                        if isinstance(options[0], dict):
                            options = [TR(TH('Value'), TH('Title'))] + \
                                      [TR(TD(o['value']),
                                          TD(o.get('title', '-')))
                                       for o in options]
                        else:
                            options = [TR(TD(o)) for o in options]
                        options = TABLE(klass='wrapid-doc', *options)
                    rows.append(TR(TD(field['name']),
                                   TD(field['required'] and 'yes' or 'no'),
                                   TD(field['type']),
                                   TD(options),
                                   TD(str(field['default'] or None)),
                                   TD(field['descr'])))
                if len(rows) > 2:
                    elems.append(TABLE(klass=self.css_class, *rows))

                rows = [CAPTION('Input representations'),
                        TR(TH('Mimetype'),
                           TH('Description'))]
                if fields and name == 'POST':
                    rows.append(TR(TD('application/x-www-form-urlencoded'),
                                   TD('URL-encoded form data parsed into'
                                      ' input fields; see above.'
                                      ' Does not allow file upload.')))
                    rows.append(TR(TD('multipart/form-data'),
                                   TD('Form data parsed into input form'
                                      ' fields; see above.'
                                      ' Allows file upload.')))
                    rows.append(TR(TD('application/json'),
                                   TD('JSON-encoded form data parsed into'
                                      ' input fields; see above.'
                                      ' Does not allow file upload.')))
                for inrepr in method.get('inreprs', []):
                    rows.append(TR(TD(inrepr['mimetype']),
                                   TD(inrepr['descr'])))
                if len(rows) > 2:
                    elems.append(TABLE(klass=self.css_class, *rows))

                rows = [CAPTION('Output representations'),
                        TR(TH('Mimetype'),
                           TH('Format'),
                           TH('Description'))]
                for outrepr in method.get('outreprs', []):
                    rows.append(TR(TD(outrepr['mimetype']),
                                   TD(outrepr['format']),
                                   TD(outrepr['descr'])))
                if len(rows) > 2:
                    elems.append(TABLE(klass=self.css_class, *rows))
        response = HTTP_OK(content_type=self.mimetype)
        response.append(str(HTML(head, BODY(*elems))))
        return response


class GET_Documentation(GET):
    """Produce this documentation of the web API
    by introspection of the source code.
    """

    fields = (StringField('resource',
                          descr='Resource to output documentation for.'),)

    outreprs = (JsonRepresentation,
                TextRepresentation,
                HtmlRepresentation)

    def get_data(self, resource, request, application):
        """Return the data to display as a data structure
        for the response generator to interpret.
        """
        values = self.parse_fields(request)
        resources = []
        data = dict(resource='Documentation',
                    documentation=dict(application=application.name,
                                       version=application.version,
                                       href=application.url),
                    href=resource.url,
                    outreprs=self.get_outrepr_links(resource, application),
                    resources=resources)
        resource_type = values.get('resource')
        for res in application.resources:
            if resource_type is not None and resource_type != res.type:
                continue
            resourcedata = dict(resource=res.type,
                                href=res.urlpath_template,
                                descr=res.descr)
            methoddata = resourcedata.setdefault('methods', dict())
            for name in HTTP_METHODS:
                try:
                    method = res.methods[name]
                except KeyError:
                    continue
                try:
                    descr = method.descr
                except (TypeError, AttributeError):
                    descr = method.__doc__ or None
                methoddata[name] = dict(descr=descr)

                # Input fields: query parameters or form fields
                if isinstance(method, FieldsMethodMixin):
                    fields = list(method.fields)
                    methoddata[name]['fields'] = [f.get_data() for f in fields]

                # Input representations
                if isinstance(method, InreprsMethodMixin):
                    rdata = []
                    inreprs = list(method.inreprs)
                    for inrepr in inreprs:
                        rdata.append(dict(mimetype=inrepr.mimetype,
                                          format=inrepr.format,
                                          descr=inrepr.__doc__))
                    if rdata:
                        methoddata[name]['inreprs'] = rdata

                # Output representations
                if isinstance(method, OutreprsMethodMixin):
                    rdata = []
                    outreprs = list(method.outreprs)
                    for outrepr in outreprs:
                        rdata.append(dict(mimetype=outrepr.mimetype,
                                          format=outrepr.format,
                                          descr=outrepr.__doc__))
                    if rdata:
                        methoddata[name]['outreprs'] = rdata
            resources.append(resourcedata)
        return data
