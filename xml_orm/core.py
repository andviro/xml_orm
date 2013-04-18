#!/usr/bin/env python
#-*- coding: utf-8 -*-

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree

from copy import deepcopy
from zipfile import ZipFile, BadZipfile
from cStringIO import StringIO
import decimal


class XML_ORM_Error(Exception):
    pass


class DefinitionError(XML_ORM_Error):
    pass


class ValidationError(XML_ORM_Error):
    pass


class SerializationError(XML_ORM_Error):
    pass


class _SortedEntry(object):
    n = 0L

    def __init__(self):
        self.sort_weight = _SortedEntry.n
        _SortedEntry.n += 1


def _iterate(root):
    if root.text is not None and root.text.strip():
        yield root.text.strip()
    for e in root:
        yield e
        if e.tail is not None and e.tail.strip():
            yield e.tail.strip()


class _Stack(list):
    def __init__(self, root):
        self.__attrs = dict(root.attrib)
        super(_Stack, self).__init__(_iterate(root))

    def take_while(self, fun, maxlen):
        res = []
        if maxlen == 'unbounded':
            maxlen = len(self)
        for x in self[:maxlen]:
            if fun(x):
                res.append(self.pop(0))
            else:
                break
        return res

    def get(self, *args, **nargs):
        return self.__attrs.get(*args, **nargs)


class SimpleField(_SortedEntry):
    u'''Базовый класс для полей в контейнере

    '''
    def __init__(self, tag=None, minOccurs=1, maxOccurs=1,
                 qualify=None,
                 getter=None,
                 setter=None,
                 is_attribute=None,
                 is_text=False,
                 insert_before=None,
                 insert_after=None, **kwargs):
        """@todo: Docstring for __init__

        :tag: @todo
        :returns: @todo

        """
        super(SimpleField, self).__init__()
        self.name = None
        self.tag = tag
        if is_attribute and is_text:
            raise DefinitionError(u"Field can't be both attribute and text data")

        self.is_attribute = is_attribute

        self.is_text = is_text

        if self.tag is not None and self.is_text:
            raise DefinitionError(u"Text stored field can't have tag name")

        if tag and tag.startswith('@'):
            if self.is_attribute is None:
                self.is_attribute = True
            elif not self.is_attribute:
                raise DefinitionError(u"Field tag contradicts with is_attribute parameter")
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
            raise DefinitionError(u"Field maxOccurs can't be 0")
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
        return unicode(etree.QName(ns, self.tag)) if ns and self.qualify else self.tag

    def to_python(self, value):
        return value

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

    def to_string(self, val):
        return unicode(val)

    def load(self, *args, **nargs):
        if self.is_attribute:
            val = self._load_attrib(*args, **nargs)
        elif self.is_text:
            val = self._load_text(*args, **nargs)
        else:
            val = self._load_element(*args, **nargs)
        return val

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
            nsmap = {None: ns} if ns is not None else None
            if ns:
                nsmap['t'] = ns
            res = etree.Element(self.tag, nsmap=nsmap)
            res.text = val
            return res

    def check_len(self, val):
        return ((self.has_default or len(val) >= self.minOccurs) and
                (self.maxOccurs == 'unbounded' or len(val) <= self.maxOccurs))


class RawField(SimpleField):
    """Docstring for RawField """

    def to_python(self, root):
        return root

    def xml(self, value, ns):
        return value


class BooleanField(SimpleField):
    """Docstring for BooleanField """

    def to_string(self, val):
        return unicode(bool(val)).lower()

    def to_python(self, value):
        return value == 'true'


class CharField(SimpleField):
    u'''
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
            raise DefinitionError(u'CharField requires max_length')
        self.max_length = max_length
        super(CharField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if len(value) > self.max_length:
            raise ValidationError(u'String too long for CharField "{0}"'
                                  .format(self.name))
        return value

    def to_string(self, val):
        s = unicode(val)
        if len(s) > self.max_length:
            raise ValueError(u'String too long for CharField "{0}"'
                             .format(self.name))
        return s


class FloatField(SimpleField):
    u'''Принимает любой объект, который можно конвертировать во float.

    '''

    def to_python(self, value):
        return float(value)

    def to_string(self, val):
        return unicode(float(val))


class DateField(SimpleField):
    u'''Принимает объект типа datetime.date

    '''

    def to_python(self, value):
        return float(value)

    def to_string(self, val):
        return unicode(val.isoformat())


class IntegerField(SimpleField):
    u'''Принимает любой объект, который можно конвертировать в int.

    '''

    def to_python(self, value):
        return int(value)

    def to_string(self, val):
        return unicode(int(val))


class DecimalField(SimpleField):
    u'''Хранит значения типа Decimal

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
            raise DefinitionError(u'DecimalField requires max_digits')
        self.max_digits = max_digits

        decimal_places = kwargs.pop('decimal_places', None)
        if decimal_places is None:
            raise DefinitionError(u'DecimalField requires decimal_places')
        self.decimal_places = decimal_places

        super(DecimalField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        try:
            return decimal.Decimal(value)
        except decimal.InvalidOperation as e:
            raise ValidationError(e)
        except:
            raise

    def to_string(self, val):
        if isinstance(val, decimal.Decimal):
            context = decimal.getcontext().copy()
            context.prec = self.max_digits
            return unicode(val.quantize(decimal.Decimal(".1") ** self.decimal_places, context=context))
        else:
            return u"{0:.{1}f}".format(val, self.decimal_places)


class ComplexField(SimpleField):
    """Docstring for ComplexField """

    def __init__(self, cls=None, *args, **kwargs):
        """@todo: to be defined

        :name: @todo
        :cls: @todo
        :*args: @todo
        :**kwargs: @todo

        """
        if 'is_attribute' in kwargs or 'is_text' in kwargs:
            if kwargs['is_attribute'] or kwargs['is_text']:
                raise DefinitionError(u"ComplexField can't be text or attribute")

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
            self.cls = type(name.capitalize(), (Schema,), self._fields)
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


def _find(lst, name):
    for i, n_v_pair in enumerate(lst):
        if name == n_v_pair[0]:
            return i
    return -1


class _MetaSchema(type):
    u''''Метакласс для XML-содержимого контейнера

    '''
    def __new__(cls, name, bases, attrs):
        """Создание класса, заполнение его полей из описания контейнера
        :returns: новый класс

        """
        parents = [b for b in bases if isinstance(b, _MetaSchema)]
        if len(parents) > 1:
            raise DefinitionError(u'Only one parent schema allowed')
        new_sup = super(_MetaSchema, cls).__new__
        new_cls = new_sup(cls, name, bases, {})

        new_meta = attrs.pop('Meta', None)
        base_meta = parents[0]._meta if len(parents) else None
        meta_attrs = dict(base_meta.__dict__) if base_meta else {}
        if new_meta:
            meta_attrs.update(new_meta.__dict__)
        new_cls._meta = type('Meta', (object,), meta_attrs)

        new_cls._fields = []
        if len(parents):
            new_attrs = [(f.name, deepcopy(f)) for f in parents[0]
                         ._fields if isinstance(f, SimpleField)]
        else:
            new_attrs = []
        for name, attr in sorted(attrs.items(),
                                 key=lambda (x, y): getattr(y, 'sort_weight', None)):
            if isinstance(attr, SimpleField):
                pos = _find(new_attrs, name)
                if pos != -1:
                    del new_attrs[pos]
                else:
                    pos = len(new_attrs)
                if attr.insert_after:
                    newpos = _find(new_attrs, attr.insert_after)
                    pos = newpos + 1 if newpos != -1 else pos
                elif attr.insert_before:
                    newpos = _find(new_attrs, attr.insert_before)
                    pos = newpos if newpos != -1 else pos
                new_attrs.insert(pos, (name, attr))
            else:
                setattr(new_cls, name, attr)
        for (name, attr) in new_attrs:
            attr.add_to_cls(new_cls, name)
            if attr.getter is not None or attr.setter is not None:
                getter = getattr(new_cls, attr.getter, None) if attr.getter else None
                setter = getattr(new_cls, attr.setter, None) if attr.setter else None
                setattr(new_cls, attr.name, property(getter, setter))

        return new_cls


class Schema(object):
    __metaclass__ = _MetaSchema

    def __init__(self, **kwargs):
        """@todo: Docstring for __init__

        :**kwargs: @todo
        :returns: @todo

        """
        if not hasattr(self._meta, 'root'):
            setattr(self._meta, 'root', self.__class__.__name__)
        for field in self._fields:
            value = None
            if field.name in kwargs:
                value = kwargs.pop(field.name)
            elif field.has_default:
                value = field.default
            elif field.maxOccurs != 1:
                value = []
            if value is not None:
                setattr(self, field.name, value)
        for name, value in kwargs.items():
            setattr(self, name, value)

    @classmethod
    def load(cls, root, active_ns=None):
        """@todo: Docstring for load

        :root: @todo
        :returns: @todo

        """
        if isinstance(root, basestring):
            try:
                root = etree.fromstring(root)
            except:
                root = etree.parse(root).getroot()
        elif hasattr(root, 'read'):
            root = etree.parse(root).getroot()

        if active_ns is not None:
            ns = active_ns
        else:
            ns = getattr(cls._meta, 'namespace', etree.QName(root).namespace)
        qn = etree.QName(ns, cls._meta.root) if ns else cls._meta.root
        if etree.QName(root) != qn:
            raise ValidationError(u'Unexpected element "{0}"'
                                  .format(etree.QName(root)))
        new_elt = cls()
        stack = _Stack(root)
        for field in new_elt._fields:
            val = field.load(stack, ns)
            if not(val) and field.has_default:
                res = field.default
            else:
                res = [field.to_python(x) for x in val]

            if field.minOccurs > len(res):
                raise ValidationError(u'Too few values for field "{0}"'
                                      .format(field.name))
            elif field.maxOccurs != 'unbounded' and len(val) > field.maxOccurs:
                raise ValidationError(u'Too many values for field "{0}"'
                                      .format(field.name))
            if field.maxOccurs != 1:
                setattr(new_elt, field.name, res)
            elif len(res):
                setattr(new_elt, field.name, res[0])
        if len(stack):
            raise ValidationError(u'Unexpected {0} nodes after last field'
                                  .format(len(stack)))
        return new_elt

    def xml(self, ns=None):
        ns = getattr(self._meta, 'namespace', None) if ns is None else ns
        nsmap = {None: ns} if ns is not None else None
        if ns:
            nsmap['t'] = ns
        root = etree.Element(self._meta.root, nsmap=nsmap)
        prev_elt = None
        for field in self._fields:
            if not hasattr(self, field.name):
                if field.minOccurs != 0:
                    raise ValidationError(u'Required field "{0}" not assigned'
                                          .format(field.name))
                else:
                    continue
            value = getattr(self, field.name)
            if isinstance(value, list):
                if not field.check_len(value):
                    raise SerializationError(u'Invalid list size {0} for field "{1}"'
                                             .format(len(value), field.name))
                value = [field.xml(v) for v in value]
            else:
                value = [field.xml(value)]

            if field.is_text:
                if prev_elt is None:
                    root.text = ' '.join(value)
                else:
                    prev_elt.tail = ' '.join(value)
            elif field.is_attribute:
                root.set(field.qname(ns), ' '.join(value))
            else:
                prev_elt = value[-1] if len(value) else prev_elt
                root.extend(value)
        return root

    def __unicode__(self):
        return unicode(etree.tostring(self.xml(),
                                      encoding=unicode,
                                      pretty_print=getattr(self._meta,
                                                           'pretty_print',
                                                           False)))

    def __repr__(self):
        return etree.tostring(self.xml(),
                              encoding=getattr(self._meta, 'encoding', 'utf-8'),
                              pretty_print=getattr(self._meta, 'pretty_print', False))

    def __str__(self):
        return etree.tostring(self.xml(),
                              encoding=getattr(self._meta, 'encoding', 'utf-8'),
                              pretty_print=getattr(self._meta, 'pretty_print', False))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.save()

    def save(self):
        pass


class Zipped(object):

    def __init__(self, *args, **kwargs):
        """@todo: Docstring for __init__
        :returns: @todo

        """
        self._storage = {}
        self._old_zip = None
        self.package = None
        super(Zipped, self).__init__(*args, **kwargs)

    @classmethod
    def load(cls, package):
        try:
            zf = ZipFile(StringIO(package))
            has_filename = False
        except BadZipfile:
            zf = ZipFile(package)
            has_filename = isinstance(package, basestring)
        entry = getattr(cls._meta, 'entry', '')
        root = zf.read(entry)
        res = super(Zipped, cls).load(root)
        res._old_zip = zf
        if has_filename:
            res.package = package
        return res

    def add_file(self, name, content):
        u''' Добавление файла в ZIP-контейнер.

        :name: Имя файла в архиве
        :content: Байтовая строка с содержимым

        Добавленные таким образом файлы сохранятся в архиве после вызова метода save().
        Рекомендуется применять, где возможно, оператор with.

        '''
        self._storage[name] = content

    def save(self):
        self.package = self.package or getattr(self._meta, 'package', '').format(self=self)
        if not self.package:
            return
        open(self.package, 'wb').write(self.raw_content)

    @property
    def raw_content(self):
        """@todo: Docstring for raw_content
        :returns: @todo

        """
        storage = StringIO()
        entry = getattr(self._meta, 'entry', None)
        with ZipFile(storage, 'w') as zf:
            if entry:
                zf.writestr(entry, str(self))
            if self._old_zip:
                for n in self._old_zip.namelist():
                    if n not in self._storage and n != entry:
                        zf.writestr(n, self._old_zip.read(n))
            for n in self._storage:
                zf.writestr(n, self._storage[n])
        return storage.getvalue()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
