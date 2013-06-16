#!/usr/bin/env python
#-*- coding: utf-8 -*-

from zipfile import ZipFile
from io import BytesIO
import sys
import os

if sys.version_info >= (3,):
    basestring = str
    unicode = str
    bytes = bytes
else:
    basestring = basestring
    unicode = unicode
    bytes = str


def _safe_str(s):
    if isinstance(s, basestring):
        if '\n' in s:
            fmt = u"u'''{0}'''"
        else:
            fmt = u"u'{0}'"
        return fmt.format(unicode(s).replace('\\', '\\\\').replace("'", "\\'"))
    elif isinstance(s, list):
        return u'[{0}]'.format(', '.join(_safe_str(x) for x in s))
    else:
        return s


class Zipped(object):

    def __init__(self, *args, **kwargs):
        """@todo: Docstring for __init__
        :returns: @todo

        """
        self._storage = {}
        self._old_zip = None
        self.package = None
        self.basedir = None
        super(Zipped, self).__init__(*args, **kwargs)

    @classmethod
    def load(cls, package):
        has_filename = False
        if isinstance(package, (basestring, bytes)):
            try:
                zf = ZipFile(package)
                has_filename = True
            except:
                zf = ZipFile(BytesIO(package))
        elif hasattr(package, 'read'):
            zf = ZipFile(package)
        else:
            raise IOError('Could not load package from {0}'.format(package))

        entry = getattr(cls._meta, 'entry', '')
        storage = dict((k, zf.read(k)) for k in zf.namelist())
        zf.close()
        newcls = super(Zipped, cls)
        if entry in storage:
            res = newcls.load(storage[entry])
        else:
            res = newcls()
        res._storage = storage
        if has_filename:
            res.basedir, res.package = os.path.split(os.path.abspath(package))
        return res

    def namelist(self):
        return self._storage.keys()

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
        return self._storage[name]

    def unlink(self, name):
        ''' Удаление файла из ZIP-контейнера.

        :name: Имя файла в архиве
        :returns: None

        '''
        del self._storage[name]

    def save(self):
        self.package = self.package or getattr(self._meta, 'package', '').format(self=self)
        self.basedir = self.basedir or os.getcwd()
        if not self.package:
            return
        open(os.path.join(self.basedir, self.package), 'wb').write(self.raw_content)

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
            for n in self._storage:
                if n != entry:
                    zf.writestr(n, self._storage[n])
        return storage.getvalue()
