#!/usr/bin/env python
#-*- coding: utf-8 -*-
import decimal
import sys
import re
from datetime import datetime
#from copy import deepcopy
from .core import DefinitionError, SerializationError, ValidationError, Schema, CoreField, _MetaSchema
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
    positional = True

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
            raise DefinitionError(
                "Field can't be both attribute and text data")

        self.is_attribute = is_attribute

        self.is_text = is_text

        self.pattern = pattern

        if self.tag is not None and self.is_text:
            raise DefinitionError("Text stored field can't have tag name")

        if tag and tag.startswith('@'):
            if self.is_attribute is None:
                self.is_attribute = True
            elif not self.is_attribute:
                raise DefinitionError(
                    "Field tag contradicts with is_attribute parameter")
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

    def serialize(self, obj, root):
        if not self.has(obj):
            if self.minOccurs != 0:
                raise SerializationError('Required field "{0}" not assigned'
                                         .format(self.name))
            else:
                return

        value, field = self.get(obj)
        if not field.check_len(value):
            raise SerializationError('Invalid occurence count {0} for field "{1}"'
                                     .format(len(value), field.name))
        if isinstance(value, list):
            value = [field.xml(v) for v in value]
        else:
            value = [field.xml(value)]

        if field.is_text:
            if not len(root):
                root.text = unicode(' '.join(value))
            else:
                root[-1].tail = unicode(' '.join(value))
        elif field.is_attribute:
            ns = root.get('xmlns', None)
            root.set(field.qname(ns), ' '.join(value))
        else:
            root.extend(value)

    def get(self, obj):
        return getattr(obj, self.name), self

    def set(self, obj, field, value):
        setattr(obj, field.name, value)

    def has(self, obj):
        return hasattr(obj, self.name)

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

    def repr(self, obj):
        val, field = self.get(obj)
        return '{0}={1!r}'.format(field.name, val)

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
            res = val.split()
        elif val is None:
            res = []
        else:
            res = [val]
        return res, self

    def _load_text(self, stack, ns):
        """@todo: Docstring for _load_text

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        return stack.take_while(lambda x: isinstance(x, basestring), 1), self

    def _load_element(self, stack, ns):
        """@todo: Docstring for _load_element

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        qn = self.qname(ns)
        return [x.text or "" for x in stack.take_while(lambda x: hasattr(x, 'tag') and x.tag == qn,
                                                       self.maxOccurs)], self

    def xml(self, value, ns=None):
        val = self.to_string(value)
        if self.is_text or self.is_attribute:
            return val
        else:
            if self.qualify:
                ns = getattr(self.schema._meta,
                             'namespace', None) if ns is None else ns
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
        return [x for x in stack.take_while(
            lambda x: hasattr(x, 'tag') and x.tag == qn,
            self.maxOccurs)], self

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
            res = unicode(val.quantize(decimal.Decimal(
                ".1") ** self.decimal_places, context=context))
        else:
            res = "{0:.{1}f}".format(val, self.decimal_places)
        return super(DecimalField, self).to_string(res)


class _LazyClass(object):

    def __init__(self, getter):
        self.getter = getter
        self._real_class = None

    def __call__(self, *args, **nargs):
        if not self._real_class:
            self._real_class = self.getter()
        return self._real_class(*args, **nargs)

    def __getattr__(self, attr):
        if not self._real_class:
            self._real_class = self.getter()
        return getattr(self._real_class, attr)


class ComplexField(SimpleField):
    """Docstring for ComplexField """

    def _get_cls(self):
        if self.ref:
            self._cls = _MetaSchema.forwards.get(self.ref)
            if not self._cls:
                raise DefinitionError('Reference {0} not found for field {1}'
                                      .format(self.ref, self.name))
        if not self._cls or len(self._fields):
            parent = self._cls or Schema
            self._fields['Meta'] = type('Meta', (object,), {'root': self._root_name})
            newname = '{0}.{1}'.format(self.schema.__name__, self.name.capitalize())
            self._cls = type(newname, (parent, ), self._fields)
            self._fields = []
        return self._cls

    cls = property(_get_cls)

    def _make_cls(self, *args, **nargs):
        return self.cls(*args, **nargs)

    def __init__(self, cls=None, *args, **kwargs):
        """@todo: to be defined

        :name: @todo
        :cls: @todo
        :*args: @todo
        :**kwargs: @todo

        """
        open('log', 'a').write('init {0} {1}\n'.format(self.__class__, cls))
        if kwargs.get('is_attribute', False) or kwargs.get('is_text', False):
            raise DefinitionError("{0} can't be text or attribute"
                                  .format(self.__class__.__name__))

        if kwargs.get('pattern', None):
            raise DefinitionError("{0} can't have a pattern"
                                  .format(self.__class__.__name__))

        self._cls = cls
        self.ref = kwargs.pop('ref', None)
        self._fields, newargs = {}, {}
        for k, v in kwargs.items():
            if isinstance(v, SimpleField):
                self._fields[k] = v
            else:
                newargs[k] = v
        newargs['is_attribute'] = newargs['is_text '] = False
        super(ComplexField, self).__init__(None, *args, **newargs)

    def add_to_cls(self, cls, name):
        """@todo: Docstring for _add_to_cls

        :cls: @todo
        :name: @todo
        :returns: @todo

        """
        self.name = name
        open('log', 'a').write('begin add {0} {1} to {2}\n'.format(self.name, self._cls, cls))

        if isinstance(self._cls, basestring):
            self._root_name = self._cls
            self._cls = Schema
            open('log', 'a').write('add0 {0} {1} {2}\n'.format(self.__class__,
                                                            self._root_name,
                                                            self._cls))
        elif self._cls is None:
            self._root_name = name
            open('log', 'a').write('wtf? {0} {1} {2}\n'.format(self.__class__,
                                                            self._root_name,
                                                            self._cls))
        elif issubclass(self._cls, Schema):
            self._root_name = getattr(self._cls._meta, 'root', None)
        else:
            raise DefinitionError('{0} {1} must be derived from Schema class'
                                  .format(self.__class__.__name__, self.name))

        if self.ref and self._cls:
            raise DefinitionError('{0} {1} must have only one of `cls` or `ref` parameters'
                                  .format(self.__class__.__name__, self.name))

        self.tag = self._root_name
        super(ComplexField, self).add_to_cls(cls, name)
        setattr(cls, name.capitalize(), staticmethod(_LazyClass(self._get_cls)))

    def xml(self, val):
        if not issubclass(self.cls, val.__class__):
            raise SerializationError('Value for ComplexField {0} must be of class {1}'
                                     .format(self.name, self.cls.__name__))
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
                                self.maxOccurs), self

    def qname(self, ns=None):
        ns = getattr(self.cls._meta, 'namespace', ns) if self.qualify else ''
        return unicode(etree.QName(ns, self.tag)) if ns and self.qualify else self.tag


class ChoiceField(ComplexField):
    positional = False

    def load(self, *args, **nargs):
        for field in self.cls._fields:
            res, subfield = field.load(*args, **nargs)
            if res:
                return res, subfield
        return [], self

    def _subn(self, fld):
        return '{0}_{1}'.format(self.name, fld.name)

    def has(self, obj):
        return any(hasattr(obj, self._subn(fld)) for fld in self.cls._fields)

    def set(self, obj, field, value):
        setattr(obj, self._subn(field), value)

    def get(self, obj):
        values = [(getattr(obj, self._subn(f)), f)
                  for f in self.cls._fields
                  if hasattr(obj, self._subn(f))]
        if not values:
            raise AttributeError('No subfields of ChoiceField {0}'.format(self.name))
        if len(values) > 1:
            raise SerializationError('ChoiceField {0} must have only one subfield assigned'
                                     .format(self.name))
        return values[0]
