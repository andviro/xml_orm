#!/usr/bin/env python
#-*- coding: utf-8 -*-
import decimal
import sys
import re
from datetime import datetime
# from copy import deepcopy
from .core import DefinitionError, SerializationError, ValidationError, Schema, CoreField, _MetaSchema
from .util import _safe_str
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
    return type('{0}.A'.format(cls.__name__), (_AttrMixin, cls), {})


def _mktext(cls):
    return type('{0}.T'.format(cls.__name__), (_TextMixin, cls), {})


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
            return super(res.__class__, res).__new__(res)
        elif (isinstance(tag, basestring) and tag.startswith('@')
              or nargs.pop('is_attribute', False)):
            res = _mkattr(cls)
            return super(res.__class__, res).__new__(res)
        else:
            res = super(SimpleField, cls).__new__(cls)
        return res

    def __init__(self, tag=None, minOccurs=1, maxOccurs=1,
                 qualify=None,
                 getter=None,
                 setter=None,
                 insert_before=None,
                 insert_after=None,
                 pattern=None,
                 default=None,
                 restrict=None,
                 doc=None,
                 **kwargs):
        """@todo: Docstring for __init__

        :tag: @todo
        :returns: @todo

        """
        super(SimpleField, self).__init__()
        self._properties = ['tag', 'minOccurs', 'maxOccurs', 'qualify', 'getter', 'setter',
                            'insert_before', 'insert_after', 'pattern',
                            'default', 'restrict', 'doc']
        self.name = None
        self.tag = tag
        self.doc = doc
        self.pattern = pattern
        self.qualify = qualify is None or qualify
        self.getter = getter
        self.setter = setter
        self.restrict = restrict
        self.minOccurs = minOccurs
        self.storage_type = 'element'
        if maxOccurs == 0:
            raise DefinitionError("Field maxOccurs can't be 0")
        self.maxOccurs = maxOccurs
        self.insert_after = insert_after
        self.insert_before = insert_before
        self.default = default

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
        if self.restrict and value not in self.restrict:
            raise SerializationError('Field {0} does not match restriction'
                                     .format(self.name))
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
        return u'{0}={1!r}'.format(self.name, val)

    def reverse(self, level):
        res = u'{0} = {1}(\n'.format(self.name, self.__class__.__name__)
        res += self.reverse_props(level + 1)
        res += u'{0})'.format(' ' * 4 * level)
        return res

    def reverse_props(self, level):
        res = u''
        for prop in self._properties:
            val = getattr(self, prop, None)
            if val is not None:
                res += u'{0}{1}={2},\n'.format(' ' * level * 4, prop, _safe_str(val))
        return res

    def load(self, stack, ns):
        val = self.consume(stack, ns)
        if not len(val) and self.default is not None and self.minOccurs > 0:
            val = (self.default
                   if isinstance(self.default, list) else [self.default])
        else:
            val = [self.to_python(x) for x in val]
            if self.restrict and not all(x in self.restrict for x in val):
                raise ValidationError('Field {0} does not match restriction'
                                      .format(self.name))

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
        self.max_length = kwargs.pop('max_length', None)
        self.min_length = kwargs.pop('min_length', 0)
        super(CharField, self).__init__(*args, **kwargs)
        self._properties.append('max_length')
        self._properties.append('min_length')

    def to_python(self, value):
        l = len(value)
        if (self.max_length is not None and l > self.max_length
                or l < self.min_length):
            raise ValidationError('Invalid string length for CharField "{0}"'
                                  .format(self.name))
        return super(CharField, self).to_python(value)

    def to_string(self, value):
        s = super(CharField, self).to_string(value)
        l = len(s)
        if (self.max_length is not None and l > self.max_length
                or l < self.min_length):
            raise ValueError('Invalid string length for CharField "{0}"'
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
        self._properties.append('format')

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
        self.max_digits = kwargs.pop('max_digits', 18)
        self.decimal_places = kwargs.pop('decimal_places', None)
        super(DecimalField, self).__init__(*args, **kwargs)
        self._properties.append('decimal_places')
        self._properties.append('max_digits')

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
                ".1") ** self.decimal_places or 28, context=context))
        else:
            res = "{0:.{1}f}".format(val, self.decimal_places or 28)
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

    mixin_class = None

    def _get_cls(self):
        if self._finalized:
            return self._cls

        if isinstance(self._cls, basestring):
            if not self._tag:
                self.tag = self._cls
                self._cls = None
            elif self._tag != self._cls:
                raise DefinitionError('Tag name "{0}" for field "{1}" contradicts '
                                      'first parameter "{2}"'
                                      .format(self._tag, self.name, self._cls))
        elif self._cls is None:
            self.tag = self._tag or self.name
        else:
            self.tag = self._tag or getattr(self._cls._meta, 'root',
                                            self._cls.__name__)

        if self.ref:
            self._cls = _MetaSchema.forwards.get(self.ref)
            if not self._cls:
                raise DefinitionError('Reference {0} not found for field {1}'
                                      .format(self.ref, self.name))
            self.tag = self._tag or getattr(self._cls._meta, 'root',
                                            self._cls.__name__)

        parent = self._cls or Schema
        self._fields['Meta'] = type('Meta', (object,), {'root': self.tag})
        newname = '{0}.{1}'.format(self.schema.__name__, self.name.capitalize())
        self._cls = type(newname, (self.mixin_class, parent) if
                         self.mixin_class else (parent, ), self._fields)
        if hasattr(parent, '__doc__'):
            self._cls.__doc__ = parent.__doc__
        elif self.doc is not None:
            self._cls.__doc__ = self.doc
        self._fields = []

        self._finalized = True
        return self._cls

    cls = property(_get_cls)

    def _make_cls(self, *args, **nargs):
        return self.cls(*args, **nargs)

    def __new__(cls, class_=None, *args, **nargs):
        tag = nargs.pop('tag', class_)
        return super(ComplexField, cls).__new__(cls, tag, *args, **nargs)

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
        self._tag = newargs.pop('tag', None)
        super(ComplexField, self).__init__(self._tag, *args, **newargs)

    def reverse_props(self, level):
        res = u''
        if self.ref:
            res += u'{0}ref={1},\n'.format(' ' * level * 4, _safe_str(self.ref))
        else:
            for fld in self.cls._fields:
                res += (u'{0}{1},\n'.format(' ' * 4 * level, fld.reverse(level)))
        res += super(ComplexField, self).reverse_props(level)
        return res

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
                raise SerializationError('Value for {0} {1} must be compatible with class {2}'
                                         .format(self.__class__.__name__,
                                                 self.name, self.cls.__name__))
            root.append(val.xml(ns=ns, tag=self.tag))

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
        if len(list(initializers)) > 1:
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
