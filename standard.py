#!/usr/bin/env python
#-*- coding: utf-8 -*-
import core
from zipfile import ZipFile
from cStringIO import StringIO
from uuid import uuid4


class Zipped(object):

    @property
    def _package(self):
        """@todo: Docstring for archive
        :returns: @todo

        """
        tpl = getattr(self._meta, 'package', None)
        if tpl is None:
            return None
        return tpl.format(self=self)

    def __init__(self, *args, **nargs):
        """@todo: Docstring for __init__
        :returns: @todo

        """
        self.__storage = StringIO()
        self.__zip = ZipFile(self.__storage, 'w')
        super(Zipped, self).__init__(*args, **nargs)

    def save(self):
        entry, fn = self._fn, self._package
        if entry is None or fn is None:
            return
        with self.__zip as zf:
            zf.writestr(entry, str(self))
        open(fn, 'wb').write(self.__storage.getvalue())


class Sender(core.Schema):
    uid = core.SimpleField(u'@идентификаторСубъекта')
    type = core.SimpleField(u'@типСубъекта', getter='get_type',
                            setter='set_type')

    def get_type(self):
        if not hasattr(self, '__type'):
            if len(self.uid) == 3:
                self.__type = u'спецоператор'
            elif len(self.uid) == 4:
                self.__type = u'налоговыйОрган'
            else:
                self.__type = u'абонент'
        return self.__type

    def set_type(self, value):
        self.__type = value

    class Meta:
        root = u'отправитель'


class SOS(Sender):
    """Docstring for SOS """

    class Meta:
        root = u'спецоператор'


class Receiver(Sender):
    """Docstring for Receiver """

    class Meta:
        root = u'получатель'


class Content(core.Schema):
    """Docstring for Content """

    filename = core.SimpleField(u'@имяФайла')

    class Meta:
        root = u'содержимое'


class Signature(Content):
    """Docstring for Sign """

    role = core.SimpleField(u'@роль', default=u'абонент')

    class Meta:
        root = u'подпись'


class Document(core.Schema):
    """Docstring for Document """

    content = core.ComplexField(Content)
    signature = core.ComplexField(Signature)

    uid = core.SimpleField(u'@идентификаторДокумента')
    type_code = core.SimpleField(u'@кодТипаДокумента', default=u'01')
    type = core.SimpleField(u'@типДокумента', default=u'счетфактура')
    compressed = core.BooleanField(u'@сжат', default=False)
    sign_required = core.BooleanField(u'@ОжидаетсяПодписьПолучателя', default=False)
    orig_filename = core.SimpleField(u'@исходноеИмяФайла')

    class Meta:
        root = u'документ'


class TransInfo(core.Schema):
    version = core.SimpleField(u'@версияФормата', default=u"ФНС:1.0")
    doc_type = core.SimpleField(u'@типДокументооборота', default=u"СчетФактура")
    doc_code = core.SimpleField(u'@кодТипаДокументооборота', default=u"20")
    doc_id = core.SimpleField(u'@идентификаторДокументооборота')
    trans_type = core.SimpleField(u'@типТранзакции', default=u'СчетФактураПродавец')
    trans_code = core.SimpleField(u'@кодТипаТранзакции', default=u'01')
    soft_version = core.SimpleField(u'@ВерсПрог', default=u'АстралОтчет 1.0')
    sender = core.ComplexField(Sender)
    sos = core.ComplexField(SOS)
    receiver = core.ComplexField(Receiver)
    document = core.ComplexField(Document, maxOccurs='unbounded')

    class Meta:
        root = u'ТрансИнф'
        encoding = 'cp1251'
        pretty_print = True
        filename = 'packageDescription.xml'


class ContainerFNS(Zipped, TransInfo):
    """Docstring for ContainerFNS """

    class Meta:
        package = ('EDI_{self.sender.uid}_{self.receiver.uid}_{self.uid}'
                   '_{self.doc_code}_{self.trans_code}_{self.document[0].type_code}.zip')


if __name__ == '__main__':
    with ContainerFNS(doc_id=uuid4().hex, uid=uuid4().hex) as ti:
        ti.sender = Sender(uid=uuid4().hex)
        ti.receiver = Receiver(uid=uuid4().hex)
        ti.sos = SOS(uid=u'2AE')
        for n in range(3):
            doc = Document()
            doc.uid = uuid4().hex
            doc.orig_filename = doc.uid + '.xml'
            doc.content = Content(filename=(doc.uid + '.bin'))
            doc.signature = Signature(filename=(uuid4().hex + '.bin'))
            ti.document.append(doc)

        print str(ti)
