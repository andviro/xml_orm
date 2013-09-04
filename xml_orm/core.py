#!/usr/bin/env python
#-*- coding: utf-8 -*-


try:
    from lxml import etree
    _has_lxml = True
except ImportError:
    from xml.etree import ElementTree as etree
    _has_lxml = False

from io import BytesIO
from copy import deepcopy
import re
import sys

from .util import _safe_str

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
        self._attrs = dict(root.attrib)
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
        return self._attrs.pop(*args, **nargs)

    def empty(self):
        return not self._attrs


def _find(lst, name):
    for i, n_v_pair in enumerate(lst):
        if name == n_v_pair[0]:
            return i
    return -1


class _MetaSchema(type):
    ''''Метакласс для XML-содержимого контейнера

    '''
    forwards = {}

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

        if 'schema' in meta_attrs and _has_lxml:
            compiled_xsd = etree.XMLSchema(etree.parse(meta_attrs['schema']))
            meta_attrs['compiled_xsd'] = compiled_xsd
        new_cls._meta = type('Meta', (object,), meta_attrs)

        new_cls._fields = []
        if len(parents):
            new_attrs = [(f.name, deepcopy(f)) for f in parents[0]
                         ._fields if issubclass(f.__class__, CoreField)]
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

        new_cls._field_index = dict(new_attrs)
        for (name, attr) in new_attrs:
            attr.add_to_cls(new_cls, name)
            if attr.getter is not None or attr.setter is not None:
                getter = getattr(new_cls, attr.getter, None) if attr.getter else None
                setter = getattr(new_cls, attr.setter, None) if attr.setter else None
                setattr(new_cls, attr.name, property(getter, setter))

        _MetaSchema.forwards[new_cls.__name__] = new_cls
        return new_cls

    def _collect_refs(self, seen=set()):
        res = []
        for fld in self._fields:
            if hasattr(fld, 'ref') and fld.ref:
                if fld.ref not in seen:
                    res.append((fld.ref, fld.cls))
                    seen.add(fld.ref)
                else:
                    continue
            if hasattr(fld, 'cls'):
                res.extend(fld.cls._collect_refs(seen))
        return res

    def reverse(self, level=0, seen=set(), ref=None):
        if level:
            res = (u'{0}(\n')
        else:
            res = u'class {0}(Schema):\n'.format(ref or self.__name__)
            if hasattr(self, '__doc__') and self.__doc__:
                res += u"{0}u'''{1}'''\n".format(' ' * 4 * (level + 1),
                                                 unicode(self.__doc__))

        for fld in self._fields:
            res += (u'{0}{1}\n'.format(' ' * 4 * (level + 1),
                                       fld.reverse(level + 1)))

        meta = getattr(self, '_meta', None)
        if meta:
            mattrs = [attr for attr in dir(meta) if not attr.startswith('_')]
            if len(mattrs):
                res += u'{0}class Meta:\n'.format(' ' * 4 * (level + 1))
                for meta_attr in mattrs:
                    if not meta_attr.startswith('_'):
                        res += u'{0}{1} = {2}\n'.format(' ' * 4 * (level + 2), meta_attr,
                                                        _safe_str(getattr(meta, meta_attr)))
        if level == 0:
            refs = self._collect_refs(seen)
            seen |= set(ref for ref, _ in refs)
            for ref, cls in refs:
                res += cls.reverse(seen=seen, ref=ref)
        return res


class Schema(_MetaSchema("BaseSchema", (object,), {})):
    def __init__(self, *args, **kwargs):
        """@todo: Docstring for __init__

        :**kwargs: @todo
        :returns: @todo

        """
        if not hasattr(self._meta, 'root'):
            setattr(self._meta, 'root', self.__class__.__name__)
        pairs = list(zip(self._fields, args))
        if len(pairs) < len(args):
            raise DefinitionError('Extra positional arguments in constructor')

        for field, value in pairs:
            field.set(self, value)

        for field in self._fields[len(pairs):]:
            value = None
            if field.name in kwargs:
                value = kwargs.pop(field.name)
            elif field.default is not None:
                value = field.default
            elif field.maxOccurs != 1:
                value = []
            field.set(self, value)

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
            raise ValidationError('Expected element "{0}", got {1}'
                                  .format(qn, etree.QName(root.tag)))
        stack = _Stack(root)
        for fld in new_elt._fields:
            values = fld.load(stack, ns)
            fld.set(new_elt, values)
            fld.check_len(new_elt, ValidationError)

        if len(stack):
            raise ValidationError('Unexpected nodes inside {0}: {1}'
                                  .format(qn, [n if isinstance(n, basestring)
                                               else n.tag for n in stack]))
        if len(stack._attrs):
            raise ValidationError('Unprocessed attributes left for {0}: {1}'
                                  .format(qn, stack._attrs.keys()))
        return new_elt

    def xml(self, ns=None, tag=None):
        ns = getattr(self._meta, 'namespace', None) if ns is None else ns
        root = etree.Element(unicode(tag or self._meta.root))
        if ns is not None:
            root.set('xmlns', ns)
        for field in self._fields:
            field.check_len(self, SerializationError)
            field.serialize(self, root)
        return root

    def _make_bytes(self, force_enc=None):
        extra_args = {}
        enc = force_enc or getattr(self._meta, 'encoding', 'utf-8')
        force_xmldecl = getattr(self._meta, 'xml_declaration', False)

        if _has_lxml:
            extra_args.update(dict(
                pretty_print=getattr(self._meta, 'pretty_print', False)
            ))

        if force_xmldecl:
            if _has_lxml:
                res = etree.tostring(self.xml(),
                                     encoding=enc,
                                     xml_declaration=True,
                                     **extra_args)
            else:
                res = (bytes('<?xml version="1.0" encoding="{0}" ?>\n'.format(enc)
                             .encode('ascii'))
                       + etree.tostring(self.xml(), encoding=enc, **extra_args))
        else:
            res = etree.tostring(self.xml(), encoding=enc, **extra_args)
        return res

    def __str__(self):
        if sys.version_info >= (3,):
            return self.__unicode__()
        else:
            return self._make_bytes()

    def __unicode__(self):
        return unicode(self._make_bytes('utf-8'), 'utf-8', 'replace')

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
