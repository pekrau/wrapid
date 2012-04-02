""" wrapid: Web Resource API server framework built on Python WSGI.

Input field classes, for query of form parameter input.
"""

from .responses import HTTP_BAD_REQUEST


FIELD_CLASS_LOOKUP = dict()             # Key: type, value: class


class Field(object):
    "Abstract input field."

    type = None

    def __init__(self, name, id=None, title=None, required=False, default=None,
                 descr=None):
        assert name
        self.name = name
        self.id = id
        self.title = title
        self.required = required
        self.default = default
        self.descr = descr

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)

    def get_data(self, override=dict()):
        """Return a dictionary containing the field definition.
        The 'override' dictionary contains parameter values
        overriding those set for the Field instance."""
        return dict(type=self.type,
                    name=self.name,
                    id=self.id,
                    title=self.title,
                    required=override.get('required', self.required),
                    default=override.get('default', self.default),
                    descr=override.get('descr', self.descr))

    def get_value(self, request, method):
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
                raise ValueError("missing value for '%s'" % self.name)
            return None

    def converter(self, value):
        "Convert and check value for validity."
        return value


def add_field_class(klass):
    assert issubclass(klass, Field)
    assert klass.type
    FIELD_CLASS_LOOKUP[klass.type] = klass


class CheckboxField(Field):
    "Simple checkbox field, yielding a boolean value."

    type = 'checkbox'

    def __init__(self, name, id=None, title=None, required=False, default=None,
                 text=None, descr=None):
        super(CheckboxField, self).__init__(name,
                                            id=id,
                                            title=title,
                                            required=required,
                                            default=default,
                                            descr=descr)
        self.text = text

    def get_data(self, override=dict()):
        result = super(CheckboxField, self).get_data(override=override)
        result['text'] = self.text
        return result

    def get_value(self, request, method):
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
        "Convert and check value for validity."
        return bool(value)

add_field_class(CheckboxField)


class BooleanField(Field):
    "Boolean field: choice between true or false."

    type = 'boolean'

    def converter(self, value):
        "Convert and check value for validity."
        value = value.lstrip()
        return value and value[0].upper() in ('Y', 'T', '1')

add_field_class(BooleanField)


class StringField(Field):
    "String input field."

    type = 'string'

    def __init__(self, name, id=None, title=None, required=False, default=None,
                 length=20, maxlength=100, descr=None):
        super(StringField, self).__init__(name,
                                          id=id,
                                          title=title,
                                          required=required,
                                          default=default,
                                          descr=descr)
        self.length = length
        self.maxlength = maxlength

    def get_data(self, override=dict()):
        result = super(StringField, self).get_data(override=override)
        result['length'] = self.length
        result['maxlength'] = self.maxlength
        return result

add_field_class(StringField)


class PasswordField(StringField):
    "Password input field."

    type = 'password'

add_field_class(PasswordField)


class IntegerField(Field):
    "Integer input field."

    type = 'integer'

    def converter(self, value):
        "Convert and check value for validity."
        if isinstance(value, basestring):
            value = value.strip()
        try:
            return int(value)
        except ValueError:
            raise KeyError

add_field_class(IntegerField)


class FloatField(Field):
    "Float input field."

    type = 'float'

    def converter(self, value):
        "Convert and check value for validity."
        if isinstance(value, basestring):
            value = value.strip()
        try:
            return float(value)
        except ValueError:
            raise KeyError

add_field_class(FloatField)


class TextField(Field):
    "Text area input field."

    type = 'text'

    def __init__(self, name, id=None, title=None, required=False, default=None,
                 rows=10, cols=80, descr=None):
        super(TextField, self).__init__(name,
                                        id=id,
                                        title=title,
                                        required=required,
                                        default=default,
                                        descr=descr)
        self.rows = rows
        self.cols = cols

    def get_data(self, override=dict()):
        "Return a dictionary containing the field definition."
        result = super(TextField, self).get_data(override=override)
        result['rows'] = self.rows
        result['cols'] = self.cols
        return result

    def converter(self, value):
        """Convert and check value for validity.
        Clean up CR-LF pairs."""
        if value:
            value = value.replace('\r\n', '\n').strip()
        return value

add_field_class(TextField)


class FileField(Field):
    "File upload field; file content and information returned as a dictionary."

    type = 'file'

    def get_value(self, request, method):
        """Return the file content and information as a dictionary.
        Raise ValueError if invalid.
        """
        try:
            value = request.fields[self.name]
            if value is None: raise KeyError
            if not value.filename: raise KeyError
            return self.converter(value)
        except KeyError:
            if self.default is not None:
                return self.default
            if self.required:
                raise ValueError("missing value for '%s'" % self.name)
            return None

    def converter(self, value):
        "Convert into a dictionary."
        return dict(value=value.file.read(),
                    filename=value.filename,
                    type=value.type)

add_field_class(FileField)


class HiddenField(Field):
    "Hidden key-value field."

    type = 'hidden'

add_field_class(HiddenField)


class SelectField(Field):
    "Select one item from a given list."

    type = 'select'

    def __init__(self, name, id=None, title=None, required=False, default=None,
                 options=[], boxes=False, check=True, descr=None):
        super(SelectField, self).__init__(name,
                                          id=id,
                                          title=title,
                                          required=required,
                                          default=default,
                                          descr=descr)
        self.options = options
        self.boxes = boxes
        self.check = check

    def get_data(self, override=dict()):
        result = super(SelectField, self).get_data(override=override)
        result['options'] = override.get('options', self.options)
        result['boxes'] = self.boxes
        return result

    def converter(self, value):
        "Convert and check value for validity."
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

add_field_class(SelectField)


class MultiSelectField(SelectField):
    "Select multiple items from a given list."

    type = 'multiselect'

    def converter(self, values):
        "Convert and check value for validity."
        if self.required and not values:
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

add_field_class(MultiSelectField)
