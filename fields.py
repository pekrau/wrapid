""" wrapid: Web Resource Application Programming Interface built on Python WSGI.

Input field classes, for query of form parameter input.
"""

import logging

from .response import HTTP_BAD_REQUEST

FIELD_LOOKUP = dict()                   # Key: type, value: class


class Field(object):
    "Abstract input field."

    type = None

    def __init__(self, name, title=None, required=False, default=None,
                 descr=None):
        assert name
        self.name = name
        self.title = title
        self.required = required
        self.default = default
        self.descr = descr

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)

    def get_data(self, default=None, fill=dict()):
        "Return a dictionary containing the field definition."
        if default is None:
            default = fill.get('default', self.default)
        return dict(type=self.type,
                    name=self.name,
                    title=self.title,
                    required=fill.get('required', self.required),
                    default=default,
                    descr=fill.get('descr', self.descr))

    def get_value(self, request):
        """Return the value converted to Python representation.
        Raise ValueError if invalid.
        """
        try:
            value = request.get_value(self.name)
            if value is None: raise KeyError
            return self.converter(value)
        except KeyError:
            if self.default is not None:
                return self.default
            if self.required:
                raise ValueError(self.name)

    def converter(self, value):
        return value


def _add(klass):
    assert issubclass(klass, Field)
    assert klass.type
    FIELD_LOOKUP[klass.type] = klass


class CheckboxField(Field):
    "Simple checkbox field, yielding a boolean value."

    type = 'checkbox'

    def __init__(self, name, title=None, required=False, default=None,
                 text=None, descr=None):
        super(CheckboxField, self).__init__(name,
                                            title=title,
                                            required=required,
                                            default=default,
                                            descr=descr)
        self.text = text

    def get_data(self, default=None, fill=dict()):
        result = super(CheckboxField, self).get_data(default=default, fill=fill)
        result['text'] = self.text
        return result

    def get_value(self, request):
        """Return the value converted to Python representation.
        Raise ValueError if invalid.
        """
        try:
            value = self.converter(request.get_value(self.name))
            if value is None: raise KeyError
            return value
        except KeyError:
            if self.default is not None:
                return self.default
            return False

    def converter(self, value):
        return bool(value)

_add(CheckboxField)


class BooleanField(Field):
    "Boolean field: choice between true or false."

    type = 'boolean'

    def converter(self, value):
        value = value.lstrip()
        return value and value[0].upper() in ('Y', 'T', '1')

_add(BooleanField)


class StringField(Field):
    "String input field."

    type = 'string'

    def __init__(self, name, title=None, required=False, default=None,
                 length=20, maxlength=100, descr=None):
        super(StringField, self).__init__(name,
                                          title=title,
                                          required=required,
                                          default=default,
                                          descr=descr)
        self.length = length
        self.maxlength = maxlength

    def get_data(self, default=None, fill=dict()):
        result = super(StringField, self).get_data(default=default, fill=fill)
        result['length'] = self.length
        result['maxlength'] = self.maxlength
        return result

_add(StringField)


class PasswordField(StringField):
    "Password input field."

    type = 'password'

_add(PasswordField)


class IntegerField(Field):
    "Integer input field."

    type = 'integer'

    def converter(self, value):
        if isinstance(value, basestring):
            value = value.strip()
        try:
            return int(value)
        except ValueError:
            raise KeyError

_add(IntegerField)


class FloatField(Field):
    "Float input field."

    type = 'float'

    def converter(self, value):
        if isinstance(value, basestring):
            value = value.strip()
        try:
            return float(value)
        except ValueError:
            raise KeyError

_add(FloatField)


class TextField(Field):
    "Text area input field."

    type = 'text'

    def __init__(self, name, title=None, required=False, default=None,
                 rows=10, cols=80, descr=None):
        super(TextField, self).__init__(name,
                                        title=title,
                                        required=required,
                                        default=default,
                                        descr=descr)
        self.rows = rows
        self.cols = cols

    def get_data(self, default=None, fill=dict()):
        "Return a dictionary containing the field definition."
        result = super(TextField, self).get_data(default=default, fill=fill)
        result['rows'] = self.rows
        result['cols'] = self.cols
        return result

    def converter(self, value):
        "Clean up CR-LF pairs."
        if value:
            value = value.replace('\r\n', '\n').strip()
        return value

_add(TextField)


class FileField(Field):
    "File upload field; file content returned as buffer value."

    type = 'file'

    def converter(self, value):
        return buffer(value)

_add(FileField)


class HiddenField(Field):
    "Hidden key-value field."

    type = 'hidden'

_add(HiddenField)


class SelectField(Field):
    "Select one item from a given list."

    type = 'select'

    def __init__(self, name, title=None, options=[], default=[], boxes=False,
                 required=False, check=True, descr=None):
        super(SelectField, self).__init__(name,
                                          title=title,
                                          required=required,
                                          default=default,
                                          descr=descr)
        self.options = options
        self.boxes = boxes
        self.check = check

    def get_data(self, default=None, fill=dict()):
        result = super(SelectField, self).get_data(default=default, fill=fill)
        result['options'] = fill.get('options', self.options)
        result['boxes'] = self.boxes
        return result

    def converter(self, value):
        if value is not None:
            value = str(value)
        if self.required:
            if value is None:
                raise ValueError('no value selected')
        if self.check:
            options = set()
            for option in self.options:
                if isinstance(option, dict):
                    options.add(option['value'])
                else:
                    options.add(option)
            if not value in options:
                raise ValueError("value '%s' not among %s" % (value, options))
        return value

_add(SelectField)


class MultiSelectField(SelectField):
    "Select multiple items from a given list."

    type = 'multiselect'

    def get_value(self, request):
        """Return the value converted to Python representation.
        Raise ValueError if invalid.
        """
        try:
            value = request.get_value(self.name)
            if not value: raise KeyError
            return self.converter(value)
        except KeyError:
            return self.default

    def converter(self, values):
        if self.required:
            if not values:
                raise ValueError('no value selected')
        if isinstance(values, basestring):
            values = [values]
        values = map(str, values)
        if self.check:
            options = set()
            for option in self.options:
                if isinstance(option, dict):
                    options.add(option['value'])
                else:
                    options.add(option)
            for value in values:
                if not value in options:
                    raise ValueError("value '%s' not an option" % value)
        return values

_add(MultiSelectField)
