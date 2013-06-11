#!/usr/bin/env python
#-*- coding: utf-8 -*-

from xml.etree import ElementTree as etree

xs = "http://www.w3.org/2001/XMLSchema"

def process(root, level=0):
    type_ref = {}
    for globaltype in root.findall('{{{0}}}complexType'.format(xs)):
        name = globaltype.get('name')
        type_ref[name] = (globaltype, j)
    for globaltype in root.findall('{{{0}}}element'.format(xs)):
        print globaltype

if __name__ == '__main__':
    xsd = etree.parse(u'logical-message-v1.xsd').getroot()

    process(xsd)
