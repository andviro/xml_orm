#!/usr/bin/env python
#-*- coding: utf-8 -*-
from xml_orm.inspect import inspect_xsd
import sys
import codecs

if sys.version_info >= (3,):
    basestring = str
    unicode = str
    bytes = bytes
else:
    basestring = basestring
    unicode = unicode
    bytes = str


def main(argv):
    if len(argv) < 3:
        print('''Usage: inspect.py schema1.xsd [schema2.xsd ...] result.py
or: inspect.py schema1.xsd [schema2.xsd ...] - ''')
        sys.exit(1)
    resfile = argv[-1]
    if resfile != '-' and not resfile.endswith('.py'):
        print('''Target file extension must be .py''')
        sys.exit(2)
    result = codecs.open(resfile, 'wb', encoding='utf-8') if resfile != '-' else sys.stdout
    result.write('# coding: utf-8\n')
    for xsd in argv[1:-1]:
        for res in inspect_xsd(unicode(xsd)):
            s = res.reverse()
            result.write(s)

if __name__ == "__main__":
    main(sys.argv)
