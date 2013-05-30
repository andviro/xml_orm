#!/usr/bin/env python
#-*- coding: utf-8 -*-
import decimal
import sys
import re
from datetime import datetime
from .core import DefinitionError, ValidationError, Schema, CoreField
try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree

if sys.version_info >= (3,):
    basestring = str
    unicode = str
    bytes = bytes
else:
    basestring = basestring
    unicode = unicode
    bytes = str


class _SortedEntry(object):
    n = 0

    def __init__(self):
        self.sort_weight = _SortedEntry.n
        _SortedEntry.n += 1


class SimpleField(_SortedEntry, CoreField):
    '''Базовый класс для полей в контейнере

    '''
    def __init__(self, tag=None, minOccurs=1, maxOccurs=1,
                 qualify=None,
                 getter=None,
                 setter=None,
                 is_attribute=None,
                 is_text=False,
                 insert_before=None,
                 insert_after=None,
                 pattern=None,
                 **kwargs):
        """@todo: Docstring for __init__

        :tag: @todo
        :returns: @todo

        """
        super(SimpleField, self).__init__()
        self.name = None
        self.tag = tag
        if is_attribute and is_text:
            raise DefinitionError("Field can't be both attribute and text data")

        self.is_attribute = is_attribute

        self.is_text = is_text

        self.pattern = pattern

        if self.tag is not None and self.is_text:
            raise DefinitionError("Text stored field can't have tag name")

        if tag and tag.startswith('@'):
            if self.is_attribute is None:
                self.is_attribute = True
            elif not self.is_attribute:
                raise DefinitionError("Field tag contradicts with is_attribute parameter")
            self.tag = tag[1:]

        self.is_attribute = (tag is None
                             and self.is_attribute is None
                             and not self.is_text
                             or self.is_attribute)

        if self.is_attribute:
            self.qualify = qualify is not None and qualify
        else:
            self.qualify = qualify is None or qualify

        self.getter = getter
        self.setter = setter
        self.minOccurs = minOccurs
        if maxOccurs == 0:
            raise DefinitionError("Field maxOccurs can't be 0")
        self.maxOccurs = maxOccurs
        self.insert_after = insert_after
        self.insert_before = insert_before
        if 'default' in kwargs:
            self.has_default = True
            self.default = kwargs['default']
        else:
            self.has_default = False

    def qname(self, ns=None):
        ns = getattr(self.schema._meta, 'namespace', '') if ns is None else ns
        return unicode(etree.QName(ns, self.tag)) if ns and self.qualify else unicode(self.tag)

    def to_python(self, value):
        if self.pattern and not re.match(self.pattern, value):
            raise ValidationError('Pattern for field "{0}" does not match'
                                  .format(self.name))
        return value

    def to_string(self, value):
        res = unicode(value)
        if self.pattern and not re.match(self.pattern, res):
            raise ValueError('Pattern for field "{0}" does not match'
                             .format(self.name))
        return res

    def add_to_cls(self, cls, name):
        """@todo: Docstring for _add_to_cls

        :cls: @todo
        :name: @todo
        :returns: @todo

        """
        self.schema = cls
        self.name = name
        self.tag = self.tag or name
        cls._fields.append(self)

    def repr(self, val):
        return '{0}={1!r}'.format(self.name, val)

    def load(self, *args, **nargs):
        if self.is_attribute:
            return self._load_attrib(*args, **nargs)
        elif self.is_text:
            return self._load_text(*args, **nargs)
        return self._load_element(*args, **nargs)

    def _load_attrib(self, stack, ns):
        """@todo: Docstring for _load_attrib

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        val = stack.get(self.qname(ns), None)
        if val is not None and self.maxOccurs != 1:
            return val.split()
        return [] if val is None else [val]

    def _load_text(self, stack, ns):
        """@todo: Docstring for _load_text

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        return stack.take_while(lambda x: isinstance(x, basestring), 1)

    def _load_element(self, stack, ns):
        """@todo: Docstring for _load_element

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        qn = self.qname(ns)
        return [x.text or "" for x in stack.take_while(lambda x: hasattr(x, 'tag') and x.tag == qn,
                                                       self.maxOccurs)]

    def xml(self, value, ns=None):
        val = self.to_string(value)
        if self.is_text or self.is_attribute:
            return val
        else:
            if self.qualify:
                ns = getattr(self.schema._meta, 'namespace', None) if ns is None else ns
            else:
                ns = ''
            res = etree.Element(self.qname(ns) if ns else self.tag)
            res.text = val
            return res

    def check_len(self, val):
        l = len(val) if isinstance(val, list) else 1
        return ((self.has_default or l >= self.minOccurs) and
                (self.maxOccurs == 'unbounded' or l <= self.maxOccurs))


class RawField(SimpleField):
    """Docstring for RawField """

    def _load_element(self, stack, ns):
        """@todo: Docstring for _load_element

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        qn = self.qname(ns)
        return [x for x in stack.take_while(lambda x: hasattr(x, 'tag') and x.tag == qn,
                                            self.maxOccurs)]

    def to_python(self, root):
        return root

    def xml(self, value, ns=None):
        return value


class BooleanField(SimpleField):
    """Docstring for BooleanField """

    def to_string(self, value):
        res = unicode(bool(value)).lower()
        return super(BooleanField, self).to_string(res)

    def to_python(self, value):
        return super(BooleanField, self).to_python(value) == 'true'


class CharField(SimpleField):
    '''
    Строковое поле с ограничением максимальной длины

    '''
    def __init__(self, *args, **kwargs):
        """@todo: Docstring for __init__

        :max_length: максимальная длина строки
        :*args: @todo
        :**kwargs: @todo
        :returns: @todo

        """
        max_length = kwargs.pop('max_length', None)
        if max_length is None:
            raise DefinitionError('CharField requires max_length')
        self.max_length = max_length
        super(CharField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if len(value) > self.max_length:
            raise ValidationError('String too long for CharField "{0}"'
                                  .format(self.name))
        return super(CharField, self).to_python(value)

    def to_string(self, value):
        s = super(CharField, self).to_string(value)
        if len(s) > self.max_length:
            raise ValueError('String too long for CharField "{0}"'
                             .format(self.name))
        return s


class FloatField(SimpleField):
    '''Принимает любой объект, который можно конвертировать во float.

    '''

    def to_python(self, value):
        return float(super(FloatField, self).to_python(value))

    def to_string(self, val):
        return super(FloatField, self).to_string(float(val))


class DateTimeField(SimpleField):
    '''
    Поле для хранения даты и/или времени

    '''
    def __init__(self, *args, **kwargs):
        """@todo: Docstring for __init__

        :format: формат для чтения/вывода в строку.
            По умолчанию "YYYY-MM-DDTHH:MM:SS"

        """
        self.format = kwargs.pop('format', u'%Y-%m-%dT%H:%M:%S')
        super(DateTimeField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        return datetime.strptime(
            super(DateTimeField, self).to_python(value),
            self.format)

    def to_string(self, val):
        return super(DateTimeField, self).to_string(val.strftime(self.format))


class IntegerField(SimpleField):
    '''Принимает любой объект, который можно конвертировать в int.

    '''

    def to_python(self, value):
        return int(super(IntegerField, self).to_python(value))

    def to_string(self, val):
        return super(IntegerField, self).to_string(int(val))


class DecimalField(SimpleField):
    '''Хранит значения типа Decimal

    '''

    def __init__(self, *args, **kwargs):
        """@todo: Docstring for __init__

        :max_digits: число значащих цифр
        :decimal_places: точность
        :*args: @todo
        :**kwargs): @todo
        :returns: @todo

        """
        max_digits = kwargs.pop('max_digits', None)
        if max_digits is None:
            raise DefinitionError('DecimalField requires max_digits')
        self.max_digits = max_digits

        decimal_places = kwargs.pop('decimal_places', None)
        if decimal_places is None:
            raise DefinitionError('DecimalField requires decimal_places')
        self.decimal_places = decimal_places

        super(DecimalField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        try:
            return decimal.Decimal(super(DecimalField, self).to_python(value))
        except decimal.InvalidOperation as e:
            raise ValidationError(e)
        except:
            raise

    def to_string(self, val):
        if isinstance(val, decimal.Decimal):
            context = decimal.getcontext().copy()
            context.prec = self.max_digits
            res = unicode(val.quantize(decimal.Decimal(".1") ** self.decimal_places, context=context))
        else:
            res = "{0:.{1}f}".format(val, self.decimal_places)
        return super(DecimalField, self).to_string(res)


class ComplexField(SimpleField):
    """Docstring for ComplexField """

    def __init__(self, cls=None, *args, **kwargs):
        """@todo: to be defined

        :name: @todo
        :cls: @todo
        :*args: @todo
        :**kwargs: @todo

        """
        if kwargs.get('is_attribute', False) or kwargs.get('is_text', False):
            raise DefinitionError("ComplexField can't be text or attribute")

        if kwargs.get('pattern', None):
            raise DefinitionError("ComplexField can't have a pattern")

        self.cls = cls
        self._fields, newargs = {}, {}
        for k, v in kwargs.items():
            if isinstance(v, SimpleField):
                self._fields[k] = v
            else:
                newargs[k] = v
        super(ComplexField, self).__init__(None, *args, **newargs)
        q = newargs.get('qualify', None)
        self.qualify = q is None or q
        self.is_attribute = self.is_text = False

    def add_to_cls(self, cls, name):
        """@todo: Docstring for _add_to_cls

        :cls: @todo
        :name: @todo
        :returns: @todo

        """
        if self.cls is None:
            self.cls = name

        if isinstance(self.cls, basestring):
            self._fields['Meta'] = type('Meta', (object,), {'root': self.cls})
            newname = '{0}.{1}'.format(cls.__name__, name.capitalize())
            self.cls = type(newname, (Schema,), self._fields)
        self.tag = getattr(self.cls._meta, 'root', None)

        super(ComplexField, self).add_to_cls(cls, name)
        setattr(cls, name.capitalize(), staticmethod(self.cls))

    def xml(self, val):
        ns = getattr(self.cls._meta, 'namespace', None) if self.qualify else ''
        return val.xml(ns=ns)

    def to_python(self, root):
        ns = getattr(self.cls._meta, 'namespace', None) if self.qualify else ''
        return self.cls.load(root, ns)

    def _load_element(self, stack, ns):
        """@todo: Docstring for _load_element

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        qn = self.qname(ns)
        return stack.take_while(lambda x: hasattr(x, 'tag') and x.tag == qn,
                                self.maxOccurs)

    def qname(self, ns=None):
        ns = getattr(self.cls._meta, 'namespace', None) if self.qualify else ''
        return unicode(etree.QName(ns, self.tag)) if ns and self.qualify else self.tag
