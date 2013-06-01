#!/usr/bin/env python
#-*- coding: utf-8 -*-

try:
    from lxml import etree
    _has_schema = True
except ImportError:
    from xml.etree import ElementTree as etree
    _has_schema = False

from io import BytesIO
from copy import deepcopy
import re
import sys

_ns_pattern = re.compile(r'{(?P<ns>[^}]+)}.*')

if sys.version_info >= (3,):
    basestring = str
    unicode = str
    bytes = bytes
else:
    basestring = basestring
    unicode = unicode
    bytes = str


class CoreField(object):
    pass


class XML_ORM_Error(Exception):
    pass


class DefinitionError(XML_ORM_Error):
    pass


class ValidationError(XML_ORM_Error):
    pass


class SerializationError(XML_ORM_Error):
    pass


def _extract_ns(root):
    """@todo: Docstring for _extract_ns

    :root: @todo
    :returns: @todo

    """
    nsobj = _ns_pattern.match(root.tag)
    return nsobj.group('ns') if nsobj else None


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


def _find(lst, name):
    for i, n_v_pair in enumerate(lst):
        if name == n_v_pair[0]:
            return i
    return -1


class _MetaSchema(type):
    ''''Метакласс для XML-содержимого контейнера

    '''
    def __new__(cls, name, bases, attrs):
        """Создание класса, заполнение его полей из описания контейнера
        :returns: новый класс

        """
        parents = [b for b in bases if isinstance(b, _MetaSchema)]
        if len(parents) > 1:
            raise DefinitionError('Only one parent schema allowed')
        new_sup = super(_MetaSchema, cls).__new__
        new_cls = new_sup(cls, name, bases, {})

        new_meta = attrs.pop('Meta', None)
        base_meta = parents[0]._meta if len(parents) else None
        meta_attrs = dict(base_meta.__dict__) if base_meta else {}
        if new_meta:
            meta_attrs.update(new_meta.__dict__)

        if 'schema' in meta_attrs and _has_schema:
            compiled_xsd = etree.XMLSchema(etree.parse(meta_attrs['schema']))
            meta_attrs['compiled_xsd'] = compiled_xsd
        new_cls._meta = type('Meta', (object,), meta_attrs)

        new_cls._fields = []
        if len(parents):
            new_attrs = [(f.name, deepcopy(f)) for f in parents[0]
                         ._fields if isinstance(f, CoreField)]
        else:
            new_attrs = []
        for name, attr in sorted(attrs.items(), key=lambda x: getattr(x[1], 'sort_weight', 0)):
            if isinstance(attr, CoreField):
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


class Schema(_MetaSchema("BaseSchema", (object,), {})):
    def __init__(self, *args, **kwargs):
        """@todo: Docstring for __init__

        :**kwargs: @todo
        :returns: @todo

        """
        if not hasattr(self._meta, 'root'):
            setattr(self._meta, 'root', self.__class__.__name__)
        pairs = list(zip((f for f in self._fields if f.positional), args))
        if len(pairs) < len(args):
            raise DefinitionError('Extra positional arguments in constructor')

        for field, value in pairs:
            setattr(self, field.name, value)

        for field in self._fields[len(pairs):]:
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
        new_elt = cls()
        if isinstance(root, unicode):
            try:
                root = etree.fromstring(root.encode('utf-8'))
            except:
                root = etree.parse(root).getroot()
        elif isinstance(root, bytes):
            cont = BytesIO(root)
            root = etree.parse(cont).getroot()
        elif hasattr(root, 'read'):
            root = etree.parse(root).getroot()

        xsd = getattr(cls._meta, 'compiled_xsd', None)
        if xsd:
            xsd.assert_(root)

        if active_ns is not None:
            ns = active_ns
        else:
            ns = getattr(new_elt._meta, 'namespace', _extract_ns(root))
        qn = etree.QName(ns, new_elt._meta.root) if ns else new_elt._meta.root
        if etree.QName(root.tag) != qn:
            raise ValidationError('Unexpected element "{0}"'
                                  .format(etree.QName(root.tag)))
        stack = _Stack(root)
        for fld in new_elt._fields:
            val, field = fld.load(stack, ns)
            if not len(val) and field.has_default and field.minOccurs > 0:
                res = (field.default
                       if isinstance(field.default, list) else [field.default])
            else:
                res = [field.to_python(x) for x in val]

            if field.minOccurs > len(res):
                raise ValidationError('Too few values for field "{0}"'
                                      .format(field.name))
            elif field.maxOccurs != 'unbounded' and len(res) > field.maxOccurs:
                raise ValidationError('Too many values for field "{0}"'
                                      .format(field.name))
            if field.maxOccurs != 1:
                fld.set(new_elt, field, res)
            elif len(res):
                fld.set(new_elt, field, res[0])
        if len(stack):
            raise ValidationError('Unexpected {0} nodes after last field'
                                  .format(len(stack)))
        return new_elt

    def xml(self, ns=None):
        ns = getattr(self._meta, 'namespace', None) if ns is None else ns
        root = etree.Element(unicode(self._meta.root))
        if ns:
            root.set('xmlns', ns)
        for field in self._fields:
            field.serialize(self, root)
        return root

    def _make_bytes(self):
        enc = getattr(self._meta, 'encoding', 'utf-8')
        force_xmldecl = getattr(self._meta, 'xml_declaration', False)
        if force_xmldecl:
            if _has_schema:
                res = etree.tostring(self.xml(), encoding=enc, xml_declaration=True)
            else:
                res = (bytes('<?xml version="1.0" encoding="{0}" ?>\n'.format(enc)
                             .encode('ascii'))
                       + etree.tostring(self.xml(), encoding=enc))
        else:
            res = etree.tostring(self.xml(), encoding=enc)
        return res

    def __str__(self):
        if sys.version_info >= (3,):
            return str(etree.tostring(self.xml(), encoding='utf-8'), 'utf-8',
                       'replace')
        else:
            return self._make_bytes()

    def __unicode__(self):
        return unicode(etree.tostring(self.xml(), encoding='utf-8'), 'utf-8')

    def __repr__(self):
        fieldrepr = ', '.join(x.repr(self) for x in self._fields if x.has(self))
        return '{0}({1})'.format(self.__class__.__name__, fieldrepr)

    def __bytes__(self):
        return self._make_bytes()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.save()

    def save(self):
        xsd = getattr(self._meta, 'compiled_xsd', None)
        if xsd:
            xsd.assert_(str(self))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
