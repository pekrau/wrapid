""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Produce the documentation for this web application by introspection.
"""

import logging
import json
import pprint
import urlparse

from HyperText.HTML40 import *

from .resource import *
from .fields import *
from .utils import HTTP_METHODS
from .json_representation import JsonRepresentation
from .text_representation import TextRepresentation


class HtmlRepresentation(Representation):
    "HTML representation suitable for display in a browser."

    mimetype = 'text/html'
    format = 'html'

    def __init__(self, css_href=None, css_class='wrapid-doc', descr=None):
        super(HtmlRepresentation, self).__init__(descr=descr)
        self.css_href = css_href
        self.css_class = css_class

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
                   klass=self.css_class),
                 P("This resource in other formats: %s." %
                   ', '.join([str(A("%(title)s (%(mimetype)s)" % r,
                                    href=r['href']))
                              for r in data['outreprs']
                              if r['mimetype'] != 'text/html']),
                   klass=self.css_class),
                 H2(data['documentation']['href'], klass=self.css_class)]
        rows = [TR(TH('Resource'),
                   TH('URL'),
                   TH('Description'))]
        for resource in data['resources']:
            title = resource['title']
            href = "#%(title)s: %(href)s" % resource
            rows.append(TR(TD(A(title, href=href)),
                           TD(resource['href']),
                           TD(resource.get('descr'))))
        elems.append(TABLE(klass=self.css_class, *rows))
        for resource in data['resources']:
            title = "%(title)s: %(href)s" % resource
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
                infields = method.get('infields', [])
                for field in infields:
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
                if infields and name == 'POST':
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
                           TH('Description'))]
                for outrepr in method.get('outreprs', []):
                    rows.append(TR(TD(outrepr['mimetype']),
                                   TD(outrepr['descr'])))
                if len(rows) > 2:
                    elems.append(TABLE(klass=self.css_class, *rows))
        response = HTTP_OK(content_type=self.mimetype)
        response.append(str(HTML(head, BODY(*elems))))
        return response


class GET_Documentation(GET):
    "Return the documentation."

    def __init__(self, css_href=None, css_class='wrapid-doc'):
        super(GET_Documentation, self).__init__(
            outreprs=[JsonRepresentation(),
                      TextRepresentation(),
                      HtmlRepresentation(css_href=css_href,
                                         css_class=css_class)],
            infields=Fields(
                StringField('resource',
                            descr='Resource to output documentation for.')),
            descr=self.__doc__)

    def get_data(self, resource, request, application):
        """Return the data to display as a data structure
        for the response generator to interpret.
        """
        values = self.infields.parse(request)
        resources = []
        data = dict(entity='documentation',
                    documentation=dict(application=application.name,
                                       version=application.version,
                                       href=application.url),
                    href=resource.url,
                    outreprs=self.get_outreprs_links(resource,
                                                     request,
                                                     application),
                    resources=resources)
        try:
            resource_name = values.get('resource')
        except AttributeError:
            resource_name = None
        for res in application.resources:
            if resource_name is not None and resource_name != res.name:
                continue
            resourcedata = dict(title=res.name,
                                href=res.urlpath_template,
                                descr=res.descr())
            methoddata = resourcedata.setdefault('methods', dict())
            for name in HTTP_METHODS:
                try:
                    method = res.methods[name]
                except KeyError:
                    continue
                try:
                    descr = method.descr()
                except (TypeError, AttributeError):
                    descr = method.__doc__ or None
                methoddata[name] = dict(descr=descr)
                # Input fields: query parameters or form fields
                try:
                    fields = list(method.infields)
                except (AttributeError, TypeError):
                    pass
                else:
                    methoddata[name]['infields'] = [f.get_data()
                                                    for f in fields]
                # Input representations
                rdata = []
                try:
                    inreprs = list(method.inreprs)
                except AttributeError:
                    try:
                        rdata.append(dict(mimetype=method.mimetype,
                                          descr=None))
                    except AttributeError:
                        pass
                else:
                    for outrepr in inreprs:
                        rdata.append(dict(mimetype=outrepr.mimetype,
                                          format=outrepr.format,
                                          descr=outrepr.descr()))
                if rdata:
                        methoddata[name]['inreprs'] = rdata
                # Output representations
                rdata = []
                try:
                    outreprs = list(method.outreprs)
                except AttributeError:
                    try:
                        rdata.append(dict(mimetype=method.mimetype,
                                          descr=None))
                    except AttributeError:
                        pass
                else:
                    for outrepr in outreprs:
                        rdata.append(dict(mimetype=outrepr.mimetype,
                                          format=outrepr.format,
                                          descr=outrepr.descr()))
                if rdata:
                        methoddata[name]['outreprs'] = rdata
            resources.append(resourcedata)
        return data
