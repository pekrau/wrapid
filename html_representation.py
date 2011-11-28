""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Base class for standard HTML representation of data.
"""

import logging
import cgi

from HyperText.HTML40 import *

try:
    import markdown
    def markdown_to_html(text):
        if text:
            return markdown.markdown(text, output_format='html4')
        else:
            return ''
except ImportError:                     # Fallback
    def markdown_to_html(text):
        return PRE(text)


from wrapid.resource import *


class BaseHtmlRepresentation(Representation):
    "Base HTML representation of the resource."

    mimetype = 'text/html'
    format = 'html'
    scripts = []
    icons = dict()

    def __call__(self, data):
        self.data = data
        self.prepare()
        html = HTML(self.get_head(),
                    BODY(TABLE(TR(TD(TABLE(TR(TD(self.get_logo())),
                                           TR(TD(self.get_navigation()))),
                                     klass='body_left'),
                                  TD(H1(self.get_title(), klass='title'),
                                     DIV(self.get_description(),
                                         klass='description'),
                                     DIV(self.get_content(),
                                         klass='content'),
                                     klass='body_middle'),
                                  TD(TABLE(TR(TD(self.get_login())),
                                           TR(TD(self.get_info())),
                                           TR(TD(self.get_operations())),
                                           TR(TD(self.get_metadata())),
                                           TR(TD(self.get_outreprs())),
                                           style='float: right;'),
                                     klass='body_right')),
                               width='100%'),
                         HR(),
                         self.get_footer(),
                         self.get_scripts()))
        response = HTTP_OK(**self.get_http_headers())
        response.append(str(html))
        return response

    def prepare(self):
        "Pre-processing before generating the HTML."
        pass

    def get_head(self):
        return HEAD(TITLE(self.get_title()),
                    META(http_equiv='Content-Type',
                         content='text/html; charset=utf-8'),
                    META(http_equiv='Content-Script-Type',
                         content='application/javascript'))

    def get_title(self):
        return self.data['title']

    def get_logo(self):
        return A(SPAN('wrapid', style='font-size: xx-large; color: green;'),
                 href=self.data['application']['href'])

    def get_description(self):
        return markdown_to_html(self.data.get('descr'))

    def get_content(self):
        return ''

    def get_operations(self):
        table = TABLE()
        for operation in self.data.get('operations', []):
            method = operation.get('method', 'GET')
            jscode = None
            if method == 'DELETE':
                override = INPUT(type='hidden',
                                 name='http_method',
                                 value=method)
                method = 'POST'
                jscode = "return confirm('Delete cannot be undone; really delete?');"
            elif method == 'PUT':
                override = INPUT(type='hidden',
                                 name='http_method',
                                 value=method)
                method = 'POST'
            else:
                override = ''
            table.append(TR(TD(FORM(self.get_submit(operation['title'],
                                                    onclick=jscode),
                                    override,
                                    method=method,
                                    action=operation['href']))))
        return table

    def get_submit(self, title, onclick=None):
        "Get the button for submit."
        try:
            icon = self.icons[title.split()[0].lower()]
        except KeyError:
            return INPUT(type='submit',
                         value=title,
                         onclick=onclick)
        else:
            return BUTTON(icon,
                          SPAN(' ', title, style='vertical-align: middle;'),
                          type='submit',
                          onclick=onclick)

    def get_navigation(self):
        table = TABLE(klass='navigation')
        current = None
        items = []
        for link in self.data.get('links', []):
            title = link['title']
            try:
                family, name = title.split(':', 1)
            except ValueError:
                if items:
                    table.append(TR(TD(family, UL(*items))))
                    items = []
                table.append(TR(TD(A(title, href=link['href']))))
            else:
                items.append(LI(A(name, href=link['href'])))
        if items:
            table.append(TR(TD(family, UL(*items))))
        return table

    def get_login(self):
        return ''

    def get_info(self):
        return ''

    def get_metadata(self):
        return ''

    def get_outreprs(self):
        table = TABLE(TR(TH('Alternative representations')),
                      klass='representations')
        for link in self.data.get('outreprs', []):
            if link['title'] == 'HTML': continue # Skip itself
            table.append(TR(TD(A(link['title'], href=link['href']))))
        return table

    def get_footer(self):
        application = self.data['application']
        host = application['host']
        return TABLE(TR(TD("%(name)s %(version)s" % application,
                           style='width:33%;'),
                        TD(A(host.get('title') or host['href'],
                             href=host['href']),
                           style='width:33%; text-align:center;'),
                        TD("%(contact)s (%(email)s)" % host,
                           style='width:33%;text-align:right;')),
                     width='100%')

    def get_scripts(self):
        result = DIV()
        for script in self.scripts:
            result.append(SCRIPT(type='text/javascript',
                                 src=self.get_url('static', script)))
        return result

    def get_form(self, fields, action,
                 values=dict(), funcs=dict(),
                 required='required', legend='',
                 klass=None, submit='Submit'):
        """Return a FORM element for editing the fields,
        which are dictionaries representing subclasses of Field.
        """
        table = TABLE(klass=klass)
        multipart = False
        for field in fields:
            if field['type'] == 'hidden': continue
            try:
                func = funcs[field['name']]
            except KeyError:
                func = ELEMENT_LOOKUP[field['type']]
            multipart = multipart or field['type'] == 'file'
            try:
                current = values[field['name']]
            except KeyError:
                current = field.get('default')
            title = field.get('title')
            if title is None:           # Allow empty string as title
                title = field['name']
            table.append(TR(TH(title),
                            TD(field.get('required') and required or ''),
                            TD(func(field, current=current)),
                            TD(I(field.get('descr') or ''))))
        hidden = []
        for field in fields:
            if field['type'] != 'hidden': continue
            current = values.get(field['name']) or field.get('default')
            func = ELEMENT_LOOKUP['hidden']
            hidden.append(func(field, current=current))
        return FORM(FIELDSET(LEGEND(legend),
                            table,
                            DIV(*hidden),
                            P(self.get_submit(submit))),
                    enctype=multipart and 'multipart/form-data'
                            or 'application/x-www-form-urlencoded',
                    method='POST',
                    action=action)

    def escape_text(self, text):
        "Return text after escaping for '&', '>' and '<' characters."
        return cgi.escape(text)


ELEMENT_LOOKUP = dict()

class Input(object):
    "INPUT element."

    translations = dict(length='size')

    def __init__(self, type, **params):
        self.type = type
        self.params = params.copy()

    def __call__(self, field, current=None):
        kwargs = dict()
        for key in self.params:
            try:
                item = field[key]
            except KeyError:
                item = self.params[key]
            if item is not None:
                kwargs[self.translations.get(key, key)] = item
        if current is not None:
            kwargs['value'] = current
        return INPUT(type=self.type, name=field['name'], **kwargs)

ELEMENT_LOOKUP['string'] = Input('text', length=20, maxlength=100)
ELEMENT_LOOKUP['password'] = Input('password', length=20, maxlength=100)
ELEMENT_LOOKUP['integer'] = Input('text', length=10, maxlength=40)
ELEMENT_LOOKUP['float'] = Input('text', length=20, maxlength=100)
ELEMENT_LOOKUP['file'] = Input('file', length=20, maxlength=100)
ELEMENT_LOOKUP['hidden'] = Input('hidden')

def get_element_boolean(field, current=None):
    if current is not None:
        if current:
            check_true = True
            check_false = False
        else:
            check_true = False
            check_false = True
    else:
        check_true = False
        check_false = False
    return TABLE(TR(TD(INPUT(type='radio', name=field['name'],
                             value='true', checked=check_true),
                       ' true '),
                    TD(INPUT(type='radio', name=field['name'],
                             value='false', checked=check_false),
                       ' false ')))
ELEMENT_LOOKUP['boolean'] = get_element_boolean

def get_element_checkbox(field, current=None):
    if current is not None:
        current = bool(current)
    return DIV(INPUT(type='checkbox', name=field['name'],
                     value='true', checked=current),
               field.get('text') or '')
ELEMENT_LOOKUP['checkbox'] = get_element_checkbox

def get_element_text(field, current=None):
    rows = field.get('rows', 20)
    cols = field.get('cols', 80)
    return TEXTAREA(current or '',
                    name=field['name'],
                    rows=rows,
                    cols=cols)
ELEMENT_LOOKUP['text'] = get_element_text


def get_element_select(field, current=None):
    elems = []
    if field['boxes']:
        for option in field['options']:
            if isinstance(option, dict):
                value = option['value']
                title = option.get('title') or value
            else:
                value = title = option
            elems.append(TR(TD(INPUT(type='radio',
                                     name=field['name'],
                                     value=value,
                                     checked=value==current or None)),
                            TD(" %s" % title)))
        return TABLE(*elems)
    else:
        for option in field['options']:
            if isinstance(option, dict):
                value = option['value']
                title = option.get('title') or value
            else:
                value = title = option
            elems.append(OPTION(title, value=value,
                                selected=value==current or None))
        return SELECT(name=field['name'], *elems)
ELEMENT_LOOKUP['select'] = get_element_select


def get_element_multiselect(field, current=None):
    if not current: current = []
    elems = []
    for option in field['options']:
        if isinstance(option, dict):
            value = option['value']
            title = option.get('title') or value
        else:
            value = title = option
        elems.append(DIV(INPUT(type='checkbox',
                               name=field['name'],
                               value=value,
                               checked=value in current),
                         title))
    return DIV(*elems)
ELEMENT_LOOKUP['multiselect'] = get_element_multiselect
