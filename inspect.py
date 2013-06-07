#!/usr/bin/env python
#-*- coding: utf-8 -*-

from xml_orm.core import Schema
from xml_orm.fields import SimpleField, ComplexField, ChoiceField, RawField


class Annotation(Schema):
    doc = SimpleField('documentation', minOccurs=0, maxOccurs='unbounded')
    text = SimpleField(is_text=True, minOccurs=0)

    class Meta:
        root = 'annotation'


class Attribute(Schema):
    name = SimpleField()
    type = SimpleField(minOccurs=0)
    doc = ComplexField(Annotation, minOccurs=0, maxOccurs='unbounded')
    type = RawField('simpleType', minOccurs=0)

    class Meta:
        root = 'attribute'


class Element(Schema):
    name = SimpleField()
    doc = ComplexField(Annotation, minOccurs=0, maxOccurs='unbounded')
    type = ComplexField(ref='ComplexType', minOccurs=0)

    class Meta:
        root = 'element'


class AnyOrElt(Schema):
    elt = ComplexField(Element, maxOccurs='unbounded')
    any = RawField()


class ComplexType(Schema):
    doc = ComplexField(Annotation, minOccurs=0, maxOccurs='unbounded')
    model = ChoiceField(
        minOccurs=0,
        sequence=ComplexField(
            elts=ChoiceField(AnyOrElt, minOccurs=0, maxOccurs='unbounded')),
        choice=ComplexField(
            elts=ChoiceField(AnyOrElt, minOccurs=0, maxOccurs='unbounded')),
    )
    attribute = ComplexField(Attribute, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        root = 'complexType'


class XSD(Schema):
    doc = ComplexField(Annotation, minOccurs=0, maxOccurs='unbounded')
    xs = ChoiceField(
        minOccurs=0,
        maxOccurs='unbounded',
        element=ComplexField(Element, maxOccurs='unbounded'),
        complex_type=ComplexField(ComplexType, maxOccurs='unbounded'),
        simple_type = RawField('simpleType', maxOccurs='unbounded'),
        imp=RawField('import'),
    )

    class Meta:
        root = 'schema'
        namespace = 'http://www.w3.org/2001/XMLSchema'


xsd = XSD.load(u'logical-message-v1.xsd')
print str(xsd)
