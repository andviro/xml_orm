#!/usr/bin/env python
#-*- coding: utf-8 -*-

from xml.etree import ElementTree as etree
from xml_orm.core import Schema
from xml_orm.fields import SimpleField, ComplexField, ChoiceField, RawField


class Attribute(Schema):
    name = SimpleField(),
    type = SimpleField(minOccurs=0),
    doc = SimpleField('annotation', minOccurs=0),
    type = RawField('simpleType', minOccurs=0),

    class Meta:
        root = 'attribute'


class Element(Schema):
    name = SimpleField(),
    doc = SimpleField('annotation', minOccurs=0),
    type = ComplexField(ref='ComplexType', minOccurs=0),

    class Meta:
        root = 'element'


class ComplexType(Schema):
    sequence = ComplexField(
        elt=ComplexField(Element, max_occurs='unbounded')),
    attribute = ComplexField(Attribute, min_occurs=0, max_occurs='unbounded')

    class Meta:
        root = 'element'


class XSD(Schema):
    xs = ChoiceField(
        element=ComplexField(Element),
    )

    class Meta:
        root = 'schema'
        namespace = 'http://www.w3.org/2001/XMLSchema'


root = etree.parse(open('TR_TRKON_2_700_01_09_02_01.xsd', 'rb')).getroot()
xsd = XSD.load(root)
print repr(xsd.xs_element)
