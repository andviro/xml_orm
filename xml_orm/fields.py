#!/usr/bin/env python
#-*- coding: utf-8 -*-
import decimal
import sys
import re
from datetime import datetime
# from copy import deepcopy
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


class _AttrMixin(object):
    def __init__(self, *args, **nargs):
        nargs['qualify'] = nargs.pop('qualify', False)
        super(_AttrMixin, self).__init__(*args, **nargs)
        self.storage_type = 'attribute'
        if isinstance(self.tag, basestring) and self.tag.startswith('@'):
            self.tag = self.tag[1:]

    def serialize(self, obj, root):
        ns = root.get('xmlns', None)
        value = self.get(obj)
        if value is None:
            return
        elif isinstance(value, list):
            value = ' '.join(self.to_string(v) for v in value)
        else:
            value = self.to_string(value)
        root.set(self.qname(ns), value)

    def consume(self, stack, ns):
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
        return res


class _TextMixin(object):
    def __init__(self, *args, **nargs):
        super(_TextMixin, self).__init__(*args, **nargs)
        if self.tag is not None:
            raise DefinitionError("Text field can't have tag name")
        self.storage_type = 'text'

    def serialize(self, obj, root):
        value = self.get(obj)
        if isinstance(value, list):
            value = ' '.join(self.to_string(v) for v in value)
        else:
            value = self.to_string(value)
        if not len(root):
            root.text = unicode(value)
        else:
            root[-1].tail = unicode(value)

    def consume(self, stack, ns):
        """@todo: Docstring for _load_text

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        return stack.take_while(lambda x: isinstance(x, basestring), 1)


def _mkattr(cls):
    return type('{0}_Attr'.format(cls.__name__), (_AttrMixin, cls), {})


def _mktext(cls):
    return type('{0}_Text'.format(cls.__name__), (_TextMixin, cls), {})


class SimpleField(_SortedEntry, CoreField):
    '''Базовый класс для полей в контейнере

    '''

    @classmethod
    def A(cls, *args, **nargs):
        real_class = _mkattr(cls)
        return real_class(*args, **nargs)

    @classmethod
    def T(cls, *args, **nargs):
        real_class = _mktext(cls)
        return real_class(*args, **nargs)

    def __new__(cls, tag=None, *args, **nargs):
        if nargs.pop('is_text', False):
            res = _mktext(cls)
            return super(res.__class__, res).__new__(res, tag, *args, **nargs)
        elif (isinstance(tag, basestring) and tag.startswith('@')
              or nargs.pop('is_attribute', False)):
            res = _mkattr(cls)
            return super(res.__class__, res).__new__(res, tag, *args, **nargs)
        else:
            res = super(SimpleField, cls).__new__(cls, tag, *args, **nargs)
        return res

    def __init__(self, tag=None, minOccurs=1, maxOccurs=1,
                 qualify=None,
                 getter=None,
                 setter=None,
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
        self.pattern = pattern
        self.qualify = qualify is None or qualify
        self.getter = getter
        self.setter = setter
        self.minOccurs = minOccurs
        self.storage_type = 'element'
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
        value = self.get(obj)
        if value is None:
            return
        elif not isinstance(value, list):
            value = [value]

        ns = root.get('xmlns', None)
        if self.qualify:
            ns = getattr(self.schema._meta,
                         'namespace', None) if ns is None else ns
        else:
            ns = ''
        for val in value:
            res = etree.Element(self.qname(ns) if ns else self.tag)
            res.text = self.to_string(val)
            root.append(res)

    def get(self, obj):
        return getattr(obj, self.name, None)

    def set(self, obj, value):
        if isinstance(value, list) and self.maxOccurs == 1:
            value = value[0] if len(value) else None
        elif value is None:
            return
        setattr(obj, self.name, value)

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
        val = self.get(obj)
        return '{0}={1!r}'.format(self.name, val)

    def load(self, stack, ns):
        val = self.consume(stack, ns)
        if not len(val) and self.has_default and self.minOccurs > 0:
            val = (self.default
                   if isinstance(self.default, list) else [self.default])
        else:
            val = [self.to_python(x) for x in val]

        return val

    def consume(self, stack, ns):
        """@todo: Docstring for _load_element

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        qn = self.qname(ns)
        return [x.text or "" for x in stack.take_while(lambda x: hasattr(x, 'tag') and x.tag == qn,
                                                       self.maxOccurs)]

    def check_len(self, obj, exc):
        values = getattr(obj, self.name, None)
        if values is None:
            l = 0
        elif not isinstance(values, list):
            l = 1
        else:
            l = len(values)
        if self.minOccurs > l:
            raise exc('Too few values for field {0}: {1}'
                      .format(self.name, l))
        elif self.maxOccurs != 'unbounded' and l > self.maxOccurs:
            raise exc('Too many values for field {0}: {1}'
                      .format(self.name, l))


class RawField(SimpleField):
    """Docstring for RawField """

    def __init__(self, *args, **kwargs):
        if kwargs.get('is_attribute', False) or kwargs.get('is_text', False):
            raise DefinitionError("{0} can't be text or attribute"
                                  .format(self.__class__.__name__))
        kwargs['is_attribute'] = kwargs['is_text'] = False
        super(RawField, self).__init__(*args, **kwargs)

    def load(self, stack, ns):
        """@todo: Docstring for _load_element

        :root: @todo
        :stack: @todo
        :ns: @todo
        :returns: @todo

        """
        qn = self.qname(ns)
        return [x for x in stack.take_while(
            lambda x: hasattr(x, 'tag') and x.tag == qn,
            self.maxOccurs)]

    def to_python(self, root):
        return root

    def serialize(self, obj, root):
        value = self.get(obj)
        if value is None:
            return
        elif not isinstance(value, list):
            value = [value]
        for val in value:
            root.append(val)


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


class _Dummy(object):
    pass


class ComplexField(SimpleField):
    """Docstring for ComplexField """

    mixin_class = _Dummy

    def _get_cls(self):
        if self._finalized:
            return self._cls

        if isinstance(self._cls, basestring):
            self.tag = self._cls
            self._cls = None
        elif self._cls is None:
            self.tag = self.name
        else:
            self.tag = getattr(self._cls._meta, 'root', None)

        if self.ref:
            self._cls = _MetaSchema.forwards.get(self.ref)
            if not self._cls:
                raise DefinitionError('Reference {0} not found for field {1}'
                                      .format(self.ref, self.name))
            self.tag = getattr(self._cls._meta, 'root', None)

        parent = self._cls or Schema
        self._fields['Meta'] = type('Meta', (object,), {'root': self.tag})
        newname = '{0}.{1}'.format(self.schema.__name__, self.name.capitalize())
        self._cls = type(newname, (self.mixin_class, parent), self._fields)
        self._fields = []

        self._finalized = True
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
        if kwargs.get('is_attribute', False) or kwargs.get('is_text', False):
            raise DefinitionError("{0} can't be text or attribute"
                                  .format(self.__class__.__name__))

        if kwargs.get('pattern', None):
            raise DefinitionError("{0} can't have a pattern"
                                  .format(self.__class__.__name__))

        self.ref = kwargs.pop('ref', None)
        if self.ref and isinstance(cls, Schema):
            raise DefinitionError('{0} {1} must have only one of `cls` or `ref` parameters'
                                  .format(self.__class__.__name__, self.name))
        self._cls = cls
        self._finalized = False
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
        if (self._cls and not isinstance(cls, basestring)
                and not issubclass(cls, Schema)):
            raise DefinitionError('Initializer for {0} {1} must be derived from Schema class'
                                  ' or string'.format(self.__class__.__name__, name))
        super(ComplexField, self).add_to_cls(cls, name)
        setattr(cls, name.capitalize(), staticmethod(_LazyClass(self._get_cls)))
        if self.storage_type != 'element':
            raise DefinitionError("{0} '{1}' cann't be text or attribute"
                                  .format(self.__class__.__name__, self.name))

    def serialize(self, obj, root):
        value = self.get(obj)
        if value is None:
            return
        elif not isinstance(value, list):
            value = [value]
        ns = getattr(self.cls._meta, 'namespace', None) if self.qualify else ''
        for val in value:
            if not issubclass(self.cls, val.__class__):
                raise SerializationError('Value for {0} {1} must be of class {2}'
                                         .format(self.__class__.__name__,
                                                 self.name, self.cls.__name__))
            root.append(val.xml(ns=ns))

    def to_python(self, root):
        ns = getattr(self.cls._meta, 'namespace', None) if self.qualify else ''
        return self.cls.load(root, ns)

    def consume(self, stack, ns):
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
        ns = getattr(self.cls._meta, 'namespace', ns) if self.qualify else ''
        return unicode(etree.QName(ns, self.tag)) if ns and self.qualify else self.tag


class _UnionMixin(object):
    def __init__(self, *args, **nargs):
        if len(args):
            raise DefinitionError("Union can't be initialized with positional"
                                  " arguments")
        initializers = zip(nargs.keys(), self._field_index.keys())
        if len(initializers) > 1:
            raise DefinitionError("Union can't be initialized with more than"
                                  " one value")
        self._field = None
        self._value = None
        super(_UnionMixin, self).__init__(*args, **nargs)

    def __setattr__(self, key, value):
        if key in self._field_index:
            self._field = self._field_index[key]
            self._value = value
        super(_UnionMixin, self).__setattr__(key, value)


class ChoiceField(ComplexField):
    mixin_class = _UnionMixin

    def load(self, stack, ns):
        res = []
        while True:
            flag = False
            for field in self.cls._fields:
                val = field.load(stack, ns)
                if len(val):
                    newelt = self.cls()
                    field.set(newelt, val)
                    field.check_len(newelt, ValidationError)
                    res.append(newelt)
                    flag = True
                    break
            if not flag:
                break
        return res

    def serialize(self, obj, root):
        value = self.get(obj)
        if value is None:
            return
        elif not isinstance(value, list):
            value = [value]
        for val in value:
            tempfld = val._field
            if not tempfld:
                continue
            tempfld.check_len(val, SerializationError)
            tempfld.serialize(val, root)
