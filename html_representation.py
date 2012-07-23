""" wrapid: Micro framework built on Python WSGI for RESTful server APIs

Base class for standard HTML 4.0 representation.
"""

import cgi

import markdown

from .HTML4 import *
from .representation import *
from .utils import url_build


class BaseHtmlRepresentation(Representation):
    "Base standard HTML representation of the resource."

    mimetype = 'text/html'
    format = 'html'
    charset = ENCODING

    logo = None                         # Relative URL
    favicon = None                      # Relative URL

    lang = 'en'                         # Primary language of page
    stylesheets = []                    # List of relative URLs;
                                        # if string, then document-level
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
                                  TD(TABLE(TR(TD(self.get_search(),
                                                 klass='search')),
                                           TR(TD(self.get_login(),
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
        response.append(DOCTYPE + '\n')
        response.append(html)
        return response

    def get_url(self, *segments, **query):
        "Return a URL based on the application URL."
        segments = [self.data['application']['href']] + list(segments)
        return url_build(*segments, **query)

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
                         content="%s; charset=%s" % (self.mimetype, ENCODING)),
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
        name = self.data['application']['name']
        if self.logo:
            content = IMG(src=self.get_url(self.logo), alt=name, title=name)
        else:
            content = SPAN(name)
        return A(content, href=self.data['application']['href'])

    def get_descr(self):
        return self.to_html(self.data.get('descr'))

    def get_navigation(self):
        table = TABLE()
        current_section = None
        items = []
        for link in self.data.get('links', []):
            title = link['title']
            image = link.get('image')
            try:
                count = " (%s)" % link['count']
            except KeyError:
                count = ''
            try:
                section, name = title.split(':', 1)
            except ValueError:
                if items:
                    if current_section:
                        table.append(TR(TD(current_section, UL(*items))))
                    else:
                        table.append(TR(TD(UL(*items))))
                        current_section = None
                    items = []
                if image:
                    content = IMG(src=image, title=title, alt=title)
                else:
                    content = title
                    if count: content += count
                table.append(TR(TD(A(content, href=link['href']))))
            else:
                if current_section != section:
                    if current_section and items:
                        table.append(TR(TD(current_section, UL(*items))))
                    items = []
                    current_section = section
                if image:
                    content = IMG(src=image, title=name, alt=name)
                else:
                    content = name
                    if count: content += count
                items.append(LI(A(content, href=link['href'])))
        if items:
            table.append(TR(TD(current_section, UL(*items))))
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
        if icon is None:
            if onclick:
                return INPUT(type=type, value=title, onclick=onclick)
            else:
                return INPUT(type=type, value=title)
        else:
            if onclick:
                return BUTTON(icon, title, type=type, onclick=onclick)
            else:
                return BUTTON(icon, title, type=type)

    def get_search(self):
        # Rather ugly; should search href be specified directly in data?
        for link in self.data['links']:
            if link['title'].lower() == 'search':
                return FORM(INPUT(type='text', name='terms',
                                  size=20, maxlength=256),
                            ## method='POST',
                            action=link['href'])
        else:
            return ''

    def get_login(self):
        login = self.data.get('login')
        if not login or login == 'anonymous':
            url = self.data.get('login_href')
            if url:
                return FORM(self.get_button('Login'),
                            INPUT(type='hidden', name='href',
                                  value=self.data.get('href', self.get_url())),
                            method='GET',
                            action=url)
            else:
                return ''
        else:
            return  DIV('Logged in as ',
                        A(login, href=self.get_url('account', login)))

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
            icon = self.get_icon(outrepr['title'].lower())
            if icon:
                table.append(TR(TD(A(icon,
                                     outrepr['title'],
                                     href=outrepr['href']))))
            else:
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

    def safe(self, text):
        "Return text after escaping '&', '>' and '<' characters."
        if text:
            return cgi.escape(text)
        else:
            return ''

    def to_html(self, text):
        "Format the text into HTML, using Markdown formatting."
        if text:
            return markdown.markdown(cgi.escape(text), output_format='html4')
        else:
            return ''


class FormHtmlMixin(object):
    "Mixin for HTML representation of the form page for data input."

    def get_content(self):
        return self.get_form()

    def get_form(self):
        "Generate the FORM element from the data."
        formdata = self.data['form']
        fields = formdata['fields']
        values = formdata.get('values', dict())
        required = self.get_icon('required') or 'required'
        multipart = False
        table = TABLE()
        for field in fields:
            if field['type'] == 'hidden': continue
            multipart = multipart or field['type'] == 'file'
            try:
                default = values[field['name']]
            except KeyError:
                default = field.get('default')
            # Allows extension to other input field types
            method = getattr(self, "get_element_%s" % field['type'])
            element = method(field, default=default)
            title = field.get('title')
            if title is None:           # Allow empty string as title
                title = field['name']
            table.append(TR(TH(title),
                            TD(field.get('required') and required or ''),
                            TD(element),
                            TD(self.to_html(field.get('descr')),klass='descr')))
        hidden = []
        for field in fields:
            if field['type'] != 'hidden': continue
            default = values.get(field['name']) or field.get('default')
            hidden.append(self.get_element_hidden(field, default))
        title = formdata.get('title')
        # Minimal input frame; no border and no cancel button
        if title is None:
            result = FORM(TABLE(TR(TD(table),
                                   TD(self.get_button(formdata.get('label',
                                                                   'Submit'))))),
                          DIV(*hidden),
                          enctype=multipart and 'multipart/form-data'
                                  or 'application/x-www-form-urlencoded',
                          method=formdata.get('method', 'POST'),
                          action=formdata['href'])
        # Ordinary input frame; border and proper buttons
        else:
            result = DIV(FORM(
                FIELDSET(LEGEND(formdata.get('title', '')),
                         table,
                         DIV(*hidden),
                         P(self.get_button(formdata.get('label', 'Submit')))),
                enctype=multipart and 'multipart/form-data'
                        or 'application/x-www-form-urlencoded',
                method=formdata.get('method', 'POST'),
                action=formdata['href']))
            cancel = formdata.get('cancel')
            if cancel:
                result.append(P(FORM(self.get_button('Cancel'),
                                     method='GET',
                                     action=cancel)))
        return result

    def get_elem_kwargs(self, field, **params):
        "Return the standard keyword arguments for an input element."
        kwargs = dict(name=field['name'])
        for key, value in params.iteritems():
            if value is not None:
                kwargs[key] = value
        for key in ['id', 'default', 'length', 'maxlength', 'rows', 'cols']:
            value = field.get(key)
            if value is not None:
                kwargs[key] = value
        try:                            # Illogically named parameters
            kwargs['value'] = kwargs.pop('default')
        except KeyError:
            pass
        try:
            kwargs['size'] = kwargs.pop('length')
        except KeyError:
            pass
        return kwargs

    def get_element_hidden(self, field, default=None):
        return INPUT(type='hidden',
                     **self.get_elem_kwargs(field, default=default))

    def get_element_string(self, field, default=None):
        return INPUT(type='text', **self.get_elem_kwargs(field,
                                                         default=default,
                                                         length=20,
                                                         maxlength=100))

    def get_element_password(self, field, default=None):
        return INPUT(type='password', **self.get_elem_kwargs(field,
                                                             default=default,
                                                             length=20,
                                                             maxlength=40))

    def get_element_integer(self, field, default=None):
        return INPUT(type='text', **self.get_elem_kwargs(field,
                                                         default=default,
                                                         length=10,
                                                         maxlength=40))

    def get_element_float(self, field, default=None):
        return INPUT(type='text', **self.get_elem_kwargs(field,
                                                         default=default,
                                                         length=20,
                                                         maxlength=100))

    def get_element_file(self, field, default=None):
        return INPUT(type='file', **self.get_elem_kwargs(field,
                                                         default=default,
                                                         length=20,
                                                         maxlength=100))

    def get_element_boolean(self, field, default=None):
        if default is not None:
            if default:
                check_true = True
                check_false = False
            else:
                check_true = False
                check_false = True
        else:
            check_true = False
            check_false = False
        kwargs = self.get_elem_kwargs(field)
        kwargs.pop('value', None)
        return TABLE(TR(TD(INPUT(type='radio', value='true',
                                 checked=check_true, **kwargs),
                           ' true '),
                        TD(INPUT(type='radio', value='false',
                                 checked=check_false, **kwargs),
                           ' false ')))

    def get_element_checkbox(self, field, default=None):
        kwargs = self.get_elem_kwargs(field)
        kwargs.pop('value', None)
        if default is not None:
            default = bool(default)
        return DIV(INPUT(type='checkbox', value='true',
                         checked=default, **kwargs),
                   field.get('text') or '')

    def get_element_text(self, field, default=None):
        kwargs = self.get_elem_kwargs(field, rows=20, cols=80)
        kwargs.pop('value', None)
        return TEXTAREA(default or '', **kwargs)

    def get_element_select(self, field, default=None):
        kwargs = self.get_elem_kwargs(field)
        kwargs.pop('value', None)       # Set below
        elems = []
        if field['boxes']:
            kwargs.pop('id', None) # 'id' cannot be set in multiple elements
            for option in field['options']:
                if isinstance(option, dict):
                    value = option['value']
                    title = option.get('title') or value
                else:
                    value = title = option
                elems.append(TR(TD(INPUT(type='radio',
                                         value=value,
                                         checked=value==default or None,
                                         **kwargs)),
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
                                    selected=value==default or None))
            return SELECT(*elems, **kwargs)

    def get_element_multiselect(self, field, default=None):
        if not default: default = []
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
                                   checked=value in default),
                             title))
        return DIV(*elems)
