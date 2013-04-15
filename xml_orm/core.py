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


class _SortedEntry(object):
    n = 0L

    def __init__(self):
        self.sort_weight = _SortedEntry.n
        _SortedEntry.n += 1


class SimpleField(_SortedEntry):
    u'''Базовый класс для полей в контейнере

    '''
    def __init__(self, tag=None, minOccurs=1, maxOccurs=1,
                 qualify=None,
                 getter=None,
                 setter=None,
                 insert_before=None,
                 insert_after=None, **kwargs):
        """@todo: Docstring for __init__

        :tag: @todo
        :returns: @todo

        """
        super(SimpleField, self).__init__()
        self.name = None
        self.tag = tag
        self.is_attribute = False
        if tag:
            self.is_attribute = tag.startswith('@')
            self.tag = tag[1:] if self.is_attribute else self.tag
        if self.is_attribute:
            self.qualify = qualify is not None and qualify
        else:
            self.qualify = qualify is None or qualify
        self.getter = getter
        self.setter = setter
        self.minOccurs = minOccurs
        assert maxOccurs, u"maxOccurs can't be 0"
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
        cls._fields.append(self)

    def to_string(self, val):
        return unicode(val)

    def load(self, root, ns):
        return self.to_python(root.text)

    def xml(self, value, ns=None):
        val = self.to_string(value)
        if self.tag is None or self.is_attribute:
            return val
        else:
            if self.qualify:
                ns = getattr(self.schema._meta, 'namespace', None) if ns is None else ns
            else:
                ns = ''
            nsmap = {None: ns, u't': ns} if ns is not None else None
            res = etree.Element(self.tag, nsmap=nsmap)
            res.text = val
            return res

    def check_len(self, val):
        res = len(val)
        assert res >= self.minOccurs, u'not enough values of field {0}'.format(self.name)
        if self.maxOccurs != 'unbounded':
            assert res <= self.maxOccurs, u'too many values of field {0}'.format(self.name)
        return res


class RawField(SimpleField):
    """Docstring for RawField """

    def load(self, root, ns):
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
        assert max_length is not None, u'CharField requires max_length'
        self.max_length = max_length
        super(CharField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        assert len(value) <= self.max_length, u'String too long for CharField'
        return value

    def to_string(self, val):
        s = unicode(val)
        assert len(s) <= self.max_length, u'String too long for CharField'
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
        assert max_digits is not None, u'required argument max_digits missing'
        self.max_digits = max_digits

        decimal_places = kwargs.pop('decimal_places', None)
        assert decimal_places is not None, u'required argument decimal_places missing'
        self.decimal_places = decimal_places

        super(DecimalField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        return decimal.Decimal(value)

    def to_string(self, val):
        if isinstance(val, decimal.Decimal):
            context = decimal.getcontext().copy()
            context.prec = self.max_digits
            return unicode(val.quantize(decimal.Decimal(".1") ** self.decimal_places, context=context))
        else:
            return u"{0:.{1}f}".format(val, self.decimal_places)


class ComplexField(SimpleField):
    """Docstring for ComplexField """

    def __init__(self, cls, *args, **kwargs):
        """@todo: to be defined

        :name: @todo
        :cls: @todo
        :*args: @todo
        :**kwargs: @todo

        """
        use_schema_ns = kwargs.pop('use_schema_ns', False)
        self.use_schema_ns = use_schema_ns
        if isinstance(cls, _MetaSchema):
            self.cls = cls
        else:
            fields, newargs = {}, {}
            for k, v in kwargs.items():
                if isinstance(v, SimpleField):
                    fields[k] = v
                else:
                    newargs[k] = v
            kwargs = newargs
            fields['Meta'] = type('Meta', (object,), {'root': cls})
            print dir(fields['Meta'])
            self.cls = type(cls, (Schema,), fields)
        super(ComplexField, self).__init__(self.cls._meta.root, *args, **kwargs)

    def add_to_cls(self, cls, name):
        """@todo: Docstring for _add_to_cls

        :cls: @todo
        :name: @todo
        :returns: @todo

        """
        super(ComplexField, self).add_to_cls(cls, name)
        setattr(cls, name.capitalize(), staticmethod(self.cls))

    def xml(self, val, ns=None):
        if not self.use_schema_ns:
            ns = getattr(self.cls._meta, 'namespace', ns) if self.qualify else ''
        return val.xml(ns=ns)

    def load(self, root, ns=None):
        if not self.use_schema_ns:
            ns = getattr(self.cls._meta, 'namespace', ns) if self.qualify else ''
        return self.cls.load(root, ns)

    def qname(self, ns=None):
        if not self.use_schema_ns:
            ns = getattr(self.cls._meta, 'namespace', ns) if self.qualify else ''
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
        assert len(parents) <= 1, u'Only one parent container type allowed'
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
        assert etree.QName(root) == qn, u'load: invalid xml tree root'
        new_elt = cls()
        n = 0
        for field in new_elt._fields:
            if field.tag is None:
                setattr(new_elt, field.name, field.to_python(root[n - 1].tail if n else root.text))
            elif field.is_attribute:
                val = root.get(field.qname(ns), None)
                assert (field.minOccurs == 0 or val is not None or field.has_default
                        ), u'required attribute {0} missing'.format(field.name)
                val = field.default if val is None and field.has_default else val
                setattr(new_elt, field.name, field.to_python(val))
            else:
                res = []
                while n < len(root):
                    if field.qname(ns) != etree.QName(root[n]):
                        break
                    res.append(field.load(root[n], ns))
                    n += 1
                if field.check_len(res):
                    setattr(new_elt, field.name, res if field.maxOccurs != 1 else res[0])
        return new_elt

    def xml(self, ns=None):
        ns = getattr(self._meta, 'namespace', None) if ns is None else ns
        nsmap = {None: ns, u't': ns} if ns is not None else None
        root = etree.Element(self._meta.root, nsmap=nsmap)
        prev_elt = None
        for field in self._fields:
            value = getattr(self, field.name, None)
            assert field.minOccurs == 0 or value is not None, u'required field {0} not assigned'.format(
                field.name)
            if value is None:
                continue
            if isinstance(value, list):
                field.check_len(value)
                value = [field.xml(v, ns) for v in value]
            else:
                value = field.xml(value, ns)
            if field.tag is None:
                if prev_elt is None:
                    root.text = value
                else:
                    prev_elt.tail = value
            elif field.is_attribute:
                root.set(field.qname(ns), ' '.join(value) if isinstance(value, list) else value)
            else:
                prev_elt = value
                if isinstance(value, list):
                    root.extend(value)
                else:
                    root.append(value)
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
