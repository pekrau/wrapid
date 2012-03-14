""" wrapid: Web Resource API server framework built on Python WSGI.

Base class for standard HTML representation of data.
"""

import cgi

from HyperText.HTML40 import *

from .response import *
from .representation import *

try:
    import markdown
    def markdown_to_html(text):
        if text:
            return markdown.markdown(cgi.escape(text), output_format='html4')
        else:
            return ''
except ImportError:                     # Fallback
    def markdown_to_html(text):
        if text:
            return PRE(cgi.escape(text))
        else:
            return ''

def safe(text):
    "Return text after escaping for '&', '>' and '<' characters."
    if text:
        return cgi.escape(text)
    else:
        return text


class BaseHtmlRepresentation(Representation):
    "Base standard HTML representation of the resource."

    mimetype = 'text/html'
    format = 'html'

    logo = None                         # Relative URL
    favicon = None                      # Relative URL

    stylesheets = []                    # List of relative URLs
                                        # If string, then document-level
                                        # stylesheet 'text/css'

    scripts = []                        # List of relative URLs

    def __call__(self, data):
        self.data = data
        self.prepare()
        html = HTML(self.get_head(),
                    BODY(TABLE(TR(TD(TABLE(TR(TD(self.get_logo(),
                                                 klass='logo')),
                                           TR(TD(self.get_navigation(),
                                                 klass='navigation'))),
                                     klass='body_left'),
                                  TD(H1(self.get_title(), klass='title'),
                                     DIV(self.get_descr(), klass='descr'),
                                     DIV(self.get_content(), klass='content'),
                                     klass='body_middle'),
                                  TD(TABLE(TR(TD(self.get_login(),
                                                 klass='login')),
                                           TR(TD(self.get_info(),
                                                 klass='info')),
                                           TR(TD(self.get_operations(),
                                                 klass='operations')),
                                           TR(TD(self.get_metadata(),
                                                 klass='metadata')),
                                           TR(TD(self.get_outreprs(),
                                                 klass='outreprs')),
                                           style='float: right;'),
                                     klass='body_right')),
                               width='100%'),
                         HR(),
                         self.get_footer(),
                         self.get_scripts()))
        response = HTTP_OK(**self.get_http_headers())
        response.append(str(html))
        return response

    def get_url(self, *segments, **query):
        "Return a URL based on the application URL."
        url = '/'.join([self.data['application']['href']] + list(segments))
        if query:
            url += '?' + urllib.urlencode(query)
        return url

    def get_icon(self, name):
        """Return the IMG element for the named icon.
        Return None if not defined.
        """
        return None

    def get_icon_labelled(self, name):
        "Return the icon IMG with name label, or just name, if no icon."
        icon = self.get_icon(name)
        if icon:
            return DIV(icon, SPAN(name), klass='icon')
        else:
            return name

    def get_ispublic(self, ispublic, labelled=True):
        "Get the access icon, labelled or not."
        key = ispublic and 'public' or 'private'
        if labelled:
            return self.get_icon_labelled(key)
        else:
            return self.get_icon(key)

    def prepare(self):
        "Prepare for generating the HTML."
        pass

    def get_head(self):
        head = HEAD(TITLE(self.get_title()),
                    META(http_equiv='Content-Type',
                         content='text/html; charset=utf-8'),
                    META(http_equiv='Content-Script-Type',
                         content='application/javascript'))
        if isinstance(self.stylesheets, str):
            head.append(STYLE("<!--\n%s\n-->\n" % self.stylesheets,
                              type='text/css'))
        else:
            for stylesheet in self.stylesheets:
                head.append(LINK(rel='stylesheet',
                                 href=self.get_url(stylesheet),
                                 type='text/css'))
        if self.favicon:
            head.append(LINK(href=self.get_url(self.favicon),
                             rel='shortcut icon'))
        return head

    def get_title(self):
        "Return the title of the page; both for header and body."
        return self.data['title']

    def get_logo(self):
        if self.logo:
            return A(IMG(src=self.get_url(self.logo),
                         alt=self.data['application']['name'],
                         title=self.data['application']['name']),
                     href=self.data['application']['href'])
        else:
            return A(SPAN('wrapid', style='font-size: xx-large; color: green;'),
                     href=self.data['application']['href'])

    def get_descr(self):
        return markdown_to_html(self.data.get('descr'))

    def get_navigation(self):
        table = TABLE()
        current = None
        items = []
        for link in self.data.get('links', []):
            title = link['title']
            try:
                section, name = title.split(':', 1)
            except ValueError:
                if items:
                    table.append(TR(TD(UL(*items))))
                    items = []
                table.append(TR(TD(A(title, href=link['href']))))
            else:
                if current != section:
                    if current and items:
                        table.append(TR(TD(current, UL(*items))))
                    items = []
                    current = section
                items.append(LI(A(name, href=link['href'])))
        if items:
            table.append(TR(TD(current, UL(*items))))
        return table

    def get_content(self):
        return ''

    def get_operations(self):
        table = TABLE()
        for operation in self.data.get('operations', []):
            if isinstance(operation, basestring): # Not a dict, i.e. a dummy
                table.append(TR(TD(operation, height=10)))
                continue
            method = operation.get('method', 'GET')
            jscode = None
            fields = []
            if method == 'DELETE':
                fields.append(INPUT(type='hidden',
                                    name='http_method',
                                    value=method))
                method = 'POST'
                jscode = "return confirm('Delete cannot be undone; really delete?');"
            elif method == 'PUT':
                fields.append(INPUT(type='hidden',
                                    name='http_method',
                                    value=method))
                method = 'POST'
            for field in operation.get('fields', []):
                fields.append(INPUT(type='hidden',
                                    name=field['name'],
                                    value=field['value']))
            table.append(TR(TD(FORM(self.get_button(operation['title'],
                                                    onclick=jscode),
                                    method=method,
                                    action=operation['href'],
                                    *fields))))
        return table

    def get_button(self, title, type='submit', onclick=None):
        "Get the button for the given type of action."
        icon = self.get_icon(title.split()[0].lower())
        if icon:
            if onclick:
                return BUTTON(icon, title, type=type, onclick=onclick)
            else:
                return BUTTON(icon, title, type=type)
        else:
            if onclick:
                return INPUT(type=type, value=title, onclick=onclick)
            else:
                return INPUT(type=type, value=title)

    def get_login(self):
        return ''

    def get_info(self):
        return ''

    def get_metadata(self):
        return ''

    def get_outreprs(self):
        outreprs = self.data.get('outreprs', [])
        outreprs = [o for o in outreprs if o['title'] != 'HTML'] # Skip itself
        if not outreprs: return ''
        table = TABLE(TR(TH('Alternative representations')))
        for outrepr in outreprs:
            table.append(TR(TD(A(outrepr['title'], href=outrepr['href']))))
        return table

    def get_footer(self):
        application = self.data['application']
        row = TR(TD("%(name)s %(version)s" % application, style='width:34%;'))
        try:
            host = application['host']
            if not host: raise KeyError
        except KeyError:
            row.append(TR(TD(style='width:67%')))
        else:
            admin = host.get('admin', '')
            try:
                admin += " (%s)" % host['email']
            except KeyError:
                pass
            try:
                link = A(host.get('title') or host['href'], href=host['href'])
            except KeyError:
                link = ''
            row.append(TD(link, style='width:33%; text-align:center;'),
                       TD(admin, style='width:33%;text-align:right;'))
        return TABLE(row, width='100%')

    def get_scripts(self):
        result = DIV()
        for script in self.scripts:
            result.append(SCRIPT(type='text/javascript',
                                 src=self.get_url(script)))
        return result

    def safe_text(self, text):
        "Return text after escaping for '&', '>' and '<' characters."
        return safe(text)


class FormHtmlMixin(object):
    "Mixin for HTML representation of the form page for data input."

    def get_content(self):
        "Generate the FORM element from the data."
        formdata = self.data['form']
        fields = formdata['fields']
        values = formdata.get('values', dict())
        table = TABLE()
        required = self.get_icon('required') or 'required'
        multipart = False
        for field in fields:
            if field['type'] == 'hidden': continue
            multipart = multipart or field['type'] == 'file'
            try:
                current = values[field['name']]
            except KeyError:
                current = field.get('default')
            title = field.get('title')
            if title is None:           # Allow empty string as title
                title = field['name']
            try:
                panel = self.get_form_field_panel(field, current=current)
            except KeyError:
                panel = ELEMENT_LOOKUP[field['type']](field, current=current)
            table.append(TR(TH(title),
                            TD(field.get('required') and required or ''),
                            TD(panel),
                            TD(markdown_to_html(field.get('descr') or ''),
                               klass='descr')))
        hidden = []
        element = ELEMENT_LOOKUP['hidden']
        for field in fields:
            if field['type'] != 'hidden': continue
            current = values.get(field['name']) or field.get('default')
            hidden.append(element(field, current=current))
        result = DIV(P(FORM(
            FIELDSET(LEGEND(formdata.get('title', '')),
                     table,
                     DIV(*hidden),
                     P(self.get_button(formdata.get('label', 'Submit')))),
            enctype=multipart and 'multipart/form-data'
                    or 'application/x-www-form-urlencoded',
            method=formdata.get('method', 'POST'),
            action=formdata['href'])))
        cancel = formdata.get('cancel')
        if cancel:
            result.append(P(FORM(self.get_button('Cancel'),
                                 method='GET',
                                 action=cancel)))
        return result

    def get_form_field_panel(self, field, current=None):
        """Return a custom panel for the given field in the form.
        Raise KeyError if no custom panel defined for the field;
        ELEMENT_LOOKUP will then be used instead.
        """
        raise KeyError


ELEMENT_LOOKUP = dict()

class Input(object):
    "INPUT element."

    translations = dict(length='size')

    def __init__(self, type, **params):
        self.type = type
        self.params = params.copy()

    def __call__(self, field, current=None):
        kwargs = dict(name=field['name'])
        id = field.get('id')
        if id is not None:
            kwargs['id'] = id
        for key in self.params:
            try:
                item = field[key]
            except KeyError:
                item = self.params[key]
            if item is not None:
                kwargs[self.translations.get(key, key)] = item
        if current is not None:
            kwargs['value'] = current
        return INPUT(type=self.type, **kwargs)

ELEMENT_LOOKUP['string'] = Input('text', length=20, maxlength=100)
ELEMENT_LOOKUP['datetime'] = Input('text', length=20, maxlength=20)
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
    kwargs = dict(name=field['name'])
    if field['id']:
        kwargs['id'] = field['id']
    return TABLE(TR(TD(INPUT(type='radio', value='true',
                             checked=check_true, **kwargs),
                       ' true '),
                    TD(INPUT(type='radio', value='false',
                             checked=check_false, **kwargs),
                       ' false ')))
ELEMENT_LOOKUP['boolean'] = get_element_boolean

def get_element_checkbox(field, current=None):
    kwargs = dict(name=field['name'])
    if field['id']:
        kwargs['id'] = field['id']
    if current is not None:
        current = bool(current)
    return DIV(INPUT(type='checkbox', value='true',
                     checked=current, **kwargs),
               field.get('text') or '')
ELEMENT_LOOKUP['checkbox'] = get_element_checkbox

def get_element_text(field, current=None):
    kwargs = dict(name=field['name'])
    if field['id']:
        kwargs['id'] = field['id']
    return TEXTAREA(current or '',
                    rows=field.get('rows', 20),
                    cols=field.get('cols', 80),
                    **kwargs)
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
            # 'id' cannot be set in multiple elements
            elems.append(TR(TD(INPUT(type='radio',
                                     name=field['name'],
                                     value=value,
                                     checked=value==current or None,
                                     **kwargs)),
                            TD(" %s" % title)))
        return TABLE(*elems)
    else:
        kwargs = dict(name=field['name'])
        if field['id']:
            kwargs['id'] = field['id']
        for option in field['options']:
            if isinstance(option, dict):
                value = option['value']
                title = option.get('title') or value
            else:
                value = title = option
            elems.append(OPTION(title, value=value,
                                selected=value==current or None))
        return SELECT(*elems, **kwargs)
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
        # 'id' cannot be set in multiple elements
        elems.append(DIV(INPUT(type='checkbox',
                               name=field['name'],
                               value=value,
                               checked=value in current),
                         title))
    return DIV(*elems)
ELEMENT_LOOKUP['multiselect'] = get_element_multiselect
