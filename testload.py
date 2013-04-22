#!/usr/bin/env python
#-*- coding: utf-8 -*-
from xml_orm.schemas.auto import autoload

import glob
import os
from hashlib import md5
from zipfile import ZipFile
from xml.etree import ElementTree as etree


def hash_xml(root, sig):
    sig.update(root.tag.encode('utf-8'))
    for name in sorted(root.attrib):
        sig.update(name.encode('utf-8'))
        sig.update(root.attrib[name].encode('utf-8'))

    if root.text is not None:
        sig.update(root.text.strip().encode('utf-8'))

    if root.tail is not None:
        sig.update(root.tail.strip().encode('utf-8'))

    for c in root.getchildren():
        hash_xml(c, sig)
    return sig.hexdigest()


def hash_zip(fn):
    res = md5()
    with ZipFile(fn) as z:
        names = sorted(z.namelist())
        for n in names:
            res.update(n.encode('utf-8'))
            if n != 'packageDescription.xml':
                res.update(z.read(n))
            else:
                t = etree.parse(z.open(n))
                hash_xml(t.getroot(), res)
    z.close()
    return res.hexdigest()


def test_load_save():
    for fn in glob.iglob('testcases/*.zip'):
        sig = hash_zip(fn)
        pkg = autoload(fn, open(fn, 'rb').read())
        print(fn)
        assert pkg is not None
        pkg.package = 'test.zip'
        pkg.save()
        sig2 = hash_zip(pkg.package)
        print(sig, sig2)
        print(pkg.package)
        os.unlink(pkg.package)
        assert sig == sig2
