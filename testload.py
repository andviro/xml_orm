#!/usr/bin/env python
#-*- coding: utf-8 -*-
from xml_orm.schemas.auto import autoload

import glob
import os
from hashlib import md5
from zipfile import ZipFile
from lxml import etree


def hash_xml(root, sig):
    sig.update(root.tag)
    for name in sorted(root.attrib):
        sig.update(name)
        sig.update(root.attrib[name])

    if root.text is not None:
        sig.update(root.text)

    if root.tail is not None:
        sig.update(root.tail)

    for c in root.getchildren():
        hash_xml(c, sig)
    return sig.hexdigest()


def hash_zip(fn):
    res = md5()
    z = ZipFile(fn)
    names = sorted(z.namelist())
    for n in names:
        res.update(n)
        if n != 'packageDescription.xml':
            res.update(z.read(n))
        else:
            parser = etree.XMLParser(remove_blank_text=True)
            t = etree.fromstring(z.read(n), parser)
            hash_xml(t, res)
    return res.hexdigest()


def test_load_save():
    for fn in glob.iglob('testcases/*.zip'):
        sig = hash_zip(fn)
        pkg = autoload(fn)
        print fn
        assert pkg is not None
        pkg.package = 'test.zip'
        pkg.save()
        sig2 = hash_zip(pkg.package)
        os.unlink(pkg.package)
        assert sig == sig2

if __name__ == "__main__":
    test_load_save()
