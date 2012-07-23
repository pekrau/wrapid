""" wrapid: Micro framework built on Python WSGI for RESTful server APIs

Documentation: static or produced for the web resource API by introspection.
"""

import time
import os.path

from .methods import *
from .html_representation import *
from .utils import HTTP_METHODS, DATETIME_WEB_FORMAT


class GET_Documentation(GET):
    """Static documentation page in Markdown format.
    The inheriting class must specify the output representations.
    """

    # To be modified in an inheriting class.
    dirpath       = None
    cache_control = None

    def prepare(self, request):
        # Default dirpath, in case class variable is not redefined
        if not self.dirpath:
            self.dirpath = os.path.join(os.path.dirname(__file__), 'docs')

    def get_data_resource(self, request):
        "Return the dictionary with the resource-specific response data."
        filename = request.variables['filename']
        filename = os.path.basename(filename) # Security
        filepath = os.path.join(self.dirpath, filename) + '.md'
        if not os.path.exists(filepath):
            raise HTTP_NOT_FOUND
        if not os.path.isfile(filepath):
            raise HTTP_NOT_FOUND
        mtime = os.path.getmtime(filepath)
        mod_file = time.strftime(DATETIME_WEB_FORMAT, time.gmtime(mtime))
        mod_since = request.headers['If-Modified-Since']
        if mod_since == mod_file:       # Don't bother comparing '<'.
            raise HTTP_NOT_MODIFIED
        return dict(title=filename.replace('_', ' '),
                    descr=open(filepath).read())


class ApiDocumentationHtmlMixin(object):
    "Mixin class to produce the HTML representation of the API documentation."

    def get_content(self):
        elems = [self.to_html(self.data['text'])]
        rows = [TR(TH('Resource'),
                   TH('URL'),
                   TH('Description'))]
        for resource in self.data['resources']:
            rows.append(TR(TD(A(resource['resource'],
                                href="#%(href)s" % resource)),
                           TD(CODE(resource['href'])),
                           TD(self.to_html(resource.get('descr')))))
        elems.append(TABLE(*rows))
        for resource in self.data['resources']:
            elems.append(H2(A("%(resource)s: %(href)s" % resource,
                              id=resource['href'])))
            elems.append(self.to_html(resource['descr']))
            for name in HTTP_METHODS:
                try:
                    method = resource['methods'][name]
                except KeyError:
                    continue
                elems.append(H3(name))
                elems.append(self.to_html(method['descr']))

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
                        options = TABLE(*options)
                    rows.append(TR(TD(field['name']),
                                   TD(field['required'] and 'yes' or 'no'),
                                   TD(field['type']),
                                   TD(options),
                                   TD(str(field['default'] or None)),
                                   TD(self.to_html(field['descr']))))
                if len(rows) > 2:
                    elems.append(TABLE(*rows))

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
                                   TD(self.to_html(inrepr['descr']))))
                if len(rows) > 2:
                    elems.append(TABLE(*rows))

                rows = [CAPTION('Output representations'),
                        TR(TH('Mimetype'),
                           TH('Format'),
                           TH('Description'))]
                for outrepr in method.get('outreprs', []):
                    rows.append(TR(TD(outrepr['mimetype']),
                                   TD(outrepr['format']),
                                   TD(self.to_html(outrepr['descr']))))
                if len(rows) > 2:
                    elems.append(TABLE(*rows))
        return DIV(klass='doc', *elems)


class GET_ApiDocumentation(GET):
    """Produce the documentation for the web resource API by introspection.
    An inheriting class must specify output representations.
    The above defined mixin ApiDocumentationHtmlMixin can be used
    to define the HTML representation.
    """

    def get_data_resource(self, request):
        "Return the data dictionary for the response."
        data = dict(title="%s %s API Documentation" %
                    (request.application.name, request.application.version),
                    href=request.url,
                    text="""This is a description of the RESTful application
programming interface (API) for this web resource. It is produced
automatically by introspection of the Python source code.

The design of the web resource is such that the set of URLs is the same for
the API and for the human user agents (browsers). This reduces complexity
and increases clarity. Usually, browsers request HTML representations,
while the JSON representation is intended for programmatic user agents.
The different representations contain the same logical data.""")
        data['resources'] = []
        for resource in request.application.resources:
            resourcedata = dict(resource=resource.name,
                                href=resource.urlpath_template,
                                descr=str(resource.descr)) # Must eval property!
            methoddata = resourcedata.setdefault('methods', dict())
            for name in HTTP_METHODS:
                try:
                    method = resource.methods[name]
                except KeyError:
                    continue
                methoddata[name] = dict(descr=method.__doc__ or None)

                # Input fields: query parameters or form fields
                if isinstance(method, FieldsMethodMixin):
                    fields = list(method.fields)
                    methoddata[name]['fields'] = [f.get_data() for f in fields]

                # Input representations
                if isinstance(method, InreprsMethodMixin):
                    reprdata = []
                    inreprs = list(method.inreprs)
                    for inrepr in inreprs:
                        reprdata.append(dict(mimetype=inrepr.mimetype,
                                             format=inrepr.format,
                                             descr=inrepr.__doc__))
                    if reprdata:
                        methoddata[name]['inreprs'] = reprdata

                # Output representations
                if isinstance(method, OutreprsMethodMixin):
                    reprdata = []
                    outreprs = list(method.outreprs)
                    for outrepr in outreprs:
                        reprdata.append(dict(mimetype=outrepr.mimetype,
                                             format=outrepr.format,
                                             descr=outrepr.__doc__))
                    if reprdata:
                        methoddata[name]['outreprs'] = reprdata
            data['resources'].append(resourcedata)
        return data
