#!/usr/bin/env python
#-*- coding: utf-8 -*-
from xml_orm.inspect import inspect_xsd
import sys


def main(argv):
    if len(argv) < 3:
        print('''Usage: inspect.py schema1.xsd [schema2.xsd ...] result.py
or: inspect.py schema1.xsd [schema2.xsd ...] - ''')
        sys.exit(1)
    resfile = argv[-1]
    if resfile != '-' and not resfile.endswith('.py'):
        print('''Target file extension must be .py''')
        sys.exit(2)
    result = open(resfile, 'wb') if resfile != '-' else sys.stdout
    result.write('# coding: utf-8\n')
    for xsd in argv[1:-1]:
        for res in inspect_xsd(unicode(xsd)):
            result.write(res.reverse().encode('utf-8'))

if __name__ == "__main__":
    main(sys.argv)
