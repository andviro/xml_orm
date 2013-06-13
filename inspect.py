#!/usr/bin/env python
#-*- coding: utf-8 -*-

from xml_orm.core import Schema, XML_ORM_Error
from xml_orm.fields import *
from xml.etree import ElementTree as etree

xs = "http://www.w3.org/2001/XMLSchema"
nsmap = {
    'xs': xs
}

QN = etree.QName


class ConversionError(XML_ORM_Error):
    pass


def inspect_complex(root, level=0, global_types={}):
    fieldnum = 1
    fields = {}
    contents = root.find('xs:sequence', namespaces=nsmap)
    if contents is not None:
        for sub in contents.findall('*', namespaces=nsmap):
            if sub.tag == QN(xs, 'element'):
                name = 'field_{0}'.format(fieldnum)
                fieldnum += 1
                fields[name] = inspect_element(sub, name, level + 1, global_types)
            elif sub.tag == QN(xs, 'sequence'):
                raise ConversionError('Nested sequences are not supported')

    for sub in root.findall('xs:attribute', namespaces=nsmap):
        props = dict(tag=sub.get('name'))
        fields['field_{0}'.format(fieldnum)] = SimpleField.A(**props)
        fieldnum += 1
    return fields


def inspect_element(root, name, level=0, global_types={}):
    t = root.find('xs:complexType', namespaces=nsmap)
    props = dict(tag=root.get('name'))
    cls = None
    if t:
        props.update(inspect_complex(t, level, global_types))
    else:
        elt_type = root.get('type')
        if elt_type and elt_type in global_types:
            cls = global_types[elt_type]
    if level == 0:
        meta = type('Meta', (object,), dict(root=props.pop('tag')))
        props['Meta'] = meta
        if isinstance(cls, type) and issubclass(cls, Schema):
            bases = (cls, )
        else:
            bases = (Schema, )
        return type(name, bases, props)
    else:
        if isinstance(cls, type) and issubclass(cls, Schema):
            props['cls'] = cls
            return ComplexField(**props)
        elif isinstance(cls, basestring):
            if cls in global_types.values():
                props['ref'] = cls
                return ComplexField(**props)
            else:
                return SimpleField(**props)


def inspect_xsd(root):
    result = []
    global_types = {}
    clsnum = 1
    for ct in root.findall('xs:complexType', namespaces=nsmap):
        name = ct.get('name')
        global_types[name] = 'Class_{0}'.format(clsnum)
        clsnum += 1
    clsnum = 1
    for ct in root.findall('xs:complexType', namespaces=nsmap):
        name = ct.get('name')
        fields = inspect_complex(ct, global_types=global_types)
        newcls = type('Class_{0}'.format(clsnum), (Schema, ), fields)
        global_types[name] = newcls
        clsnum += 1
    for elt in root.findall('xs:element', namespaces=nsmap):
        name = 'Class_{0}'.format(clsnum)
        clsnum += 1
        newcls = inspect_element(elt, name, global_types=global_types)
        if newcls:
            result.append(newcls)
    return result

if __name__ == '__main__':
    xsd = etree.parse(u'TR_TRKON_2_700_01_09_02_01.xsd')
    for res in inspect_xsd(xsd.getroot()):
        s = res.reverse(ref=res.__name__)
        compile(s, '<string>', 'exec')
        print s

