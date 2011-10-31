"""wrapid: Web Resource Application Programming Interface built on Python WSGI.

HTML-oriented utility functions.
"""

import logging

from HyperText.HTML40 import *


def get_form(fields, action, values=dict(), funcs=dict(),
             required='required', legend='', klass=None, submit='Submit'):
    """Return a FORM element for editing the fields,
    which are dictionaries representing subclasses of Field.
    """
    rows = []
    multipart = False
    for field in fields:
        try:
            func = funcs[field['name']]
        except KeyError:
            func = ELEMENT_LOOKUP[field['type']]
        multipart = multipart or field['type'] == 'file'
        current = values.get(field['name']) or field.get('default')
        rows.append(TR(TH(field.get('title') or field['name']),
                       TD(field.get('required') and required or ''),
                       TD(func(field, current=current)),
                       TD(I(field.get('descr') or ''))))
    return FORM(FIELDSET(LEGEND(legend),
                         TABLE(klass=klass, *rows),
                         P(INPUT(type='submit', value=submit))),
                enctype=multipart and 'multipart/form-data'
                        or 'application/x-www-form-urlencoded',
                method='POST',
                action=action)


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
        logging.debug("field %s %s", field['name'], kwargs)
        return INPUT(type=self.type, name=field['name'], **kwargs)

ELEMENT_LOOKUP['string'] = Input('text', length=20, maxlength=100)
ELEMENT_LOOKUP['password'] = Input('password', length=20, maxlength=100)
ELEMENT_LOOKUP['integer'] = Input('text', length=10, maxlength=40)
ELEMENT_LOOKUP['float'] = Input('text', length=20, maxlength=100)
ELEMENT_LOOKUP['file'] = Input('file', length=20, maxlength=100)

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
