#!/usr/bin/env python
#-*- coding: utf-8 -*-

from lxml import etree
from copy import deepcopy
from zipfile import ZipFile, BadZipfile
from cStringIO import StringIO


class _SortedEntry(object):
    n = 0L

    def __init__(self):
        self.sort_weight = _SortedEntry.n
        _SortedEntry.n += 1


class SimpleField(_SortedEntry):
    u'''Базовый класс для полей в контейнере

    '''
    def __init__(self, tag=None, minOccurs=1, maxOccurs=1,
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

    def load_one(self, root):
        """@todo: Docstring for load

        :obj: @todo
        :root: @todo
        :returns: @todo

        """
        ns = getattr(self.schema._meta, 'namespace', '')
        qn = etree.QName(ns, self.tag) if ns else self.tag
        if qn == etree.QName(root):
            return self.to_python(root)
        else:
            return None

    def validate(self, value):
        return value

    def add_to_cls(self, cls, name):
        """@todo: Docstring for _add_to_cls

        :cls: @todo
        :name: @todo
        :returns: @todo

        """
        self.schema = cls
        self.name = name
        cls._fields_ref[name] = self
        cls._fields.append(self)

    def to_string(self, val):
        return unicode(val)

    def to_python(self, root):
        return root.text

    def xml(self, value):
        val = self.to_string(value)
        if self.tag is None or self.tag.startswith('@'):
            return val
        else:
            nsmap = {None: getattr(self.schema._meta, 'namespace', '')}
            res = etree.Element(self.tag, nsmap=nsmap)
            res.text = val
            return res

    def check_len(self, val):
        assert len(val) >= self.minOccurs, u'not enough values of field {0}'.format(self.name)
        if self.maxOccurs != 'unbounded':
            assert len(val) <= self.maxOccurs, u'too many values of field {0}'.format(self.name)


class BooleanField(SimpleField):
    """Docstring for BooleanField """

    def to_string(self, val):
        return unicode(val).lower()

    def to_python(self, root):
        return root.text == 'true'


class ComplexField(SimpleField):
    """Docstring for ComplexField """

    def __init__(self, cls, *args, **kwargs):
        """@todo: to be defined

        :name: @todo
        :cls: @todo
        :*args: @todo
        :**kwargs: @todo

        """
        super(ComplexField, self).__init__(tag=cls._meta.root, *args, **kwargs)
        self._cls = cls

    def validate(self, value):
        assert isinstance(value, self._cls)
        return value

    def xml(self, val):
        return self.validate(val).xml()

    def to_python(self, root):
        return self._cls.load(root)

    def load_one(self, root):
        """@todo: Docstring for load

        :obj: @todo
        :root: @todo
        :returns: @todo

        """
        ns = getattr(self._cls._meta, 'namespace', '')
        qn = etree.QName(ns, self._cls._meta.root) if ns else self._cls._meta.root
        if unicode(qn) == unicode(etree.QName(root)):
            return self.to_python(root)
        else:
            return None


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
        new_cls._fields_ref = {}
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
        for name, field in self._fields_ref.items():
            value = None
            if name in kwargs:
                value = field.validate(kwargs.pop(name))
            elif field.has_default:
                value = field.validate(field.default)
            elif field.maxOccurs != 1:
                value = []
            if value is not None:
                setattr(self, name, value)
        for name, value in kwargs.items():
            setattr(self, name, value)

    @classmethod
    def load(cls, root):
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
        ns = getattr(cls._meta, 'namespace', '')
        qn = etree.QName(ns, cls._meta.root) if ns else cls._meta.root
        assert etree.QName(root) == qn, u'load: invalid xml tree root'
        new_elt = cls()
        n = 0
        for field in new_elt._fields:
            if field.tag is None:
                if n:
                    setattr(new_elt, field.name, root[n - 1].tail)
                else:
                    setattr(new_elt, field.name, root.text)
            elif field.tag.startswith('@'):
                setattr(new_elt, field.name, root.attrib[field.tag[1:]])
            else:
                if field.maxOccurs == 1:
                    val = field.load_one(root[n])
                    if val is None:
                        assert field.minOccurs == 0, u'load: required field {0} not found'.format(
                            field.name)
                    else:
                        n += 1
                    setattr(new_elt, field.name, val)
                else:
                    res = []
                    while n < len(root):
                        val = field.load_one(root[n])
                        if val is None:
                            break
                        res.append(val)
                        n += 1
                    field.check_len(res)
                    setattr(new_elt, field.name, res)
        return new_elt

    def xml(self):
        nsmap = {None: getattr(self._meta, 'namespace', '')}
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
                value = [field.xml(v) for v in value]
            else:
                value = field.xml(value)
            if field.tag is None:
                if prev_elt is None:
                    root.text = value
                else:
                    prev_elt.tail = value
            elif field.tag.startswith('@'):
                root.attrib[field.tag[1:]] = ' '.join(value) if isinstance(value, list) else value
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

    def data(self):
        return str(self)

    def save(self):
        pass


class Zipped(object):

    def __init__(self, *args, **nargs):
        """@todo: Docstring for __init__
        :returns: @todo

        """
        self._storage = StringIO()
        self._zip = ZipFile(self._storage, 'w')
        self._old_zip = None
        self.package = None
        super(Zipped, self).__init__(*args, **nargs)

    @classmethod
    def load(cls, package):
        try:
            zf = ZipFile(StringIO(package))
        except BadZipfile:
            zf = ZipFile(package)
        entry = getattr(cls._meta, 'entry', '')
        root = zf.read(entry)
        res = super(Zipped, cls).load(root)
        res._old_zip = zf
        res.package = package
        return res

    def save(self):
        self.package = self.package or getattr(self._meta, 'package', '').format(self=self)
        entry = getattr(self._meta, 'entry', '')
        if not self.package or not entry:
            return
        with self._zip as zf:
            zf.writestr(entry, str(self))
            if self._old_zip:
                new_names = frozenset(zf.namelist())
                for n in self._old_zip.namelist():
                    if n not in new_names:
                        zf.writestr(n, self._old_zip.read(n))
        open(self.package, 'wb').write(self._storage.getvalue())


if __name__ == '__main__':
    import doctest
    doctest.testmod()
