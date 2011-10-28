"""wrapid: Web Resource Application Programming Interface built on Python WSGI.

Input field classes, for query of form parameter input.
"""

import logging

from .response import HTTP_BAD_REQUEST


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

    def get_data(self, default=None, fill=dict()):
        "Return a dictionary containing the field definition."
        if default is None:
            if self.default is None:
                default = fill.get('default')
            else:
                default = self.default
        return dict(type=self.type,
                    name=self.name,
                    title=self.title,
                    required=self.required,
                    default=default,
                    descr=self.descr or fill.get('descr'))

    def get_value(self, request):
        """Return the value converted to Python representation.
        Raise ValueError if invalid.
        """
        try:
            return self.converter(request.fields[self.name].value)
        except (KeyError, AttributeError):
            if self.default is not None:
                return self.default
            if self.required:
                raise ValueError(self.name)

    def converter(self, value):
        return value


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
            return self.converter(request.fields[self.name].value)
        except (KeyError, AttributeError):
            if self.default is not None:
                return self.default
            return False

    def converter(self, value):
        return bool(value)


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


class PasswordField(StringField):
    "Password input field."

    type = 'password'


class IntegerField(Field):
    "Integer input field."

    type = 'integer'

    def converter(self, value):
        return int(value.strip())


class FloatField(Field):
    "Float input field."

    type = 'float'

    def converter(self, value):
        return float(value.strip())


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


class FileField(Field):
    "File upload field."

    type = 'file'

    def get_value(self, request):
        """Return the value converted to Python representation.
        Raise ValueError if invalid.
        """
        try:
            field = request.fields[self.name]
            if not field.file: raise AttributeError
            return field.value
        except (KeyError, AttributeError):
            if self.default is not None:
                return self.default
            if self.required:
                raise ValueError(self.name)


class SelectField(Field):
    "Select one item from a given list."

    type = 'select'

    def __init__(self, name, title=None, choices=[], default=[], required=False,
                 check=True, descr=None):
        super(SelectField, self).__init__(name,
                                          title=title,
                                          required=required,
                                          default=default,
                                          descr=descr)
        self.choices = choices
        self.check = check

    def get_data(self, default=None, fill=dict()):
        result = super(SelectField, self).get_data(default=default, fill=fill)
        result['choices'] = self.choices or fill.get('choices', [])
        return result

    def converter(self, value):
        if value is not None:
            value = str(value)
        if self.required:
            if value is None:
                raise ValueError('no value selected')
        if self.check:
            choices = set()
            for choice in self.choices:
                if isinstance(choice, dict):
                    choices.add(choice['value'])
                else:
                    choices.add(choice)
            if not value in choices:
                raise ValueError("value '%s' not among %s" % (value, choices))
        return value


class MultiSelectField(SelectField):
    "Select multiple items from a given list."

    type ='multiselect'

    def get_value(self, request):
        """Return the value converted to Python representation.
        Raise ValueError if invalid.
        """
        try:
            return self.converter(request.fields.getlist(self.name))
        except (KeyError, AttributeError):
            return self.default

    def converter(self, values):
        values = map(str, values)
        if self.required:
            if not values:
                raise ValueError('no value selected')
        if self.check:
            choices = set()
            for choice in self.choices:
                if isinstance(choice, dict):
                    choices.add(choice['value'])
                else:
                    choices.add(choice)
            for value in values:
                if not value in choices:
                    raise ValueError("value '%s' not a choice %s" %
                                     (value, choices))
        return values


class Fields(object):
    "Input fields handler."

    def __init__(self, *fields):
        self.fields = []
        self.lookup = dict()
        map(self.append, fields)

    def __iter__(self):
        return iter(self.fields)

    def append(self, field):
        if field.name in self.lookup:
            raise ValueError("field name '%s' already in use" % field.name)
        self.fields.append(field)
        self.lookup[field.name] = field

    def get_data(self, default=dict(), fill=dict()):
        return [f.get_data(default=default.get(f.name),
                           fill=fill.get(f.name, dict()))
                for f in self.fields]

    def parse(self, request):
        """Parse out the values from the input fields.
        Raise HTTP_BAD_REQUEST if any problem.
        """
        result = dict()
        for field in self.fields:
            try:
                result[field.name] = field.get_value(request)
            except ValueError, msg:
                logging.error("wrapid: parsing field %s, %s", field.name, msg)
                raise HTTP_BAD_REQUEST(str(msg))
        return result
