#!/usr/bin/env python
#-*- coding: utf-8 -*-

from zipfile import ZipFile
from io import BytesIO
import sys

if sys.version_info >= (3,):
    basestring = str
    unicode = str
    bytes = bytes
else:
    basestring = basestring
    unicode = unicode
    bytes = str


class Zipped(object):

    def __init__(self, *args, **kwargs):
        """@todo: Docstring for __init__
        :returns: @todo

        """
        self._storage = {}
        self._old_zip = None
        self.package = None
        super(Zipped, self).__init__(*args, **kwargs)

    @classmethod
    def load(cls, package):
        zf = ZipFile(package)
        has_filename = isinstance(package, basestring)
        entry = getattr(cls._meta, 'entry', '')
        root = zf.read(entry)
        res = super(Zipped, cls).load(root)
        res._old_zip = zf
        if has_filename:
            res.package = package
        return res

    def write(self, name, content):
        ''' Запись файла в ZIP-контейнер.

        :name: Имя файла в архиве
        :content: Байтовая строка с содержимым

        Добавленные таким образом файлы сохранятся в архиве после вызова метода save().
        Рекомендуется применять, где возможно, оператор with.

        '''
        self._storage[name] = content

    def read(self, name):
        ''' Извлечение файла из ZIP-контейнера.

        :name: Имя файла в архиве
        :returns: Байтовая строка с содержимым

        '''
        if name in self._storage:
            return self._storage[name]
        return self._old_zip.read(name)

    def save(self):
        self.package = self.package or getattr(self._meta, 'package', '').format(self=self)
        if not self.package:
            return
        open(self.package, 'wb').write(self.raw_content)

    @property
    def raw_content(self):
        """@todo: Docstring for raw_content
        :returns: @todo

        """
        storage = BytesIO()
        entry = getattr(self._meta, 'entry', None)
        with ZipFile(storage, 'w') as zf:
            if entry:
                zf.writestr(entry, bytes(self))
            if self._old_zip:
                for n in self._old_zip.namelist():
                    if n not in self._storage and n != entry:
                        zf.writestr(n, self._old_zip.read(n))
            for n in self._storage:
                zf.writestr(n, self._storage[n])
        return storage.getvalue()
