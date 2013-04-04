#!/usr/bin/env python
#-*- coding: utf-8 -*-
import core
from zipfile import ZipFile
from uuid import uuid4


class Zipped(object):

    @property
    def _archive(self):
        """@todo: Docstring for archive
        :returns: @todo

        """
        tpl = getattr(self._meta, 'archive', None)
        if tpl is None:
            return None
        return tpl.format(self=self)

    def save(self):
        print 'save_zipped'
        entry, fn = self._fn, self._archive
        if entry is None or fn is None:
            return
        with ZipFile(fn, 'w') as zf:
            zf.writestr(entry, str(self))


class Sender(core.Schema):
    uid = core.SimpleField(u'@идентификаторСубъекта')
    type = core.SimpleField(u'@типСубъекта', default=u'абонент')

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

    @classmethod
    def create(self, *args, **kwargs):
        """@todo: Docstring for create

        :*args: @todo
        :**kwargs: @todo
        :returns: @todo

        """
        if 'doc_id' not in kwargs:
            kwargs['doc_id'] = uuid4().hex
        res = super(TransInfo, self).create(*args, **kwargs)
        res._uid = uuid4().hex
        return res


class ContainerFNS(Zipped, TransInfo):
    """Docstring for ContainerFNS """

    class Meta:
        archive = 'EDI_{self.sender.uid}_{self.receiver.uid}_{self._uid}_{self.doc_code}_{self.trans_code}_{self.document[0].type_code}.zip'


if __name__ == '__main__':
    with ContainerFNS.create() as ti:
        ti.sender = Sender(uid=u'default_sender')
        ti.receiver = Receiver(uid=u'defaut_receiver')
        ti.sos = SOS(uid=u'2AE')
        for n in range(3):
            doc = Document()
            doc.uid = uuid4().hex
            doc.orig_filename = doc.uid + '.xml'
            doc.content = Content(filename=(doc.uid + '.bin'))
            doc.signature = Signature(filename=(uuid4().hex + '.bin'))
            ti.document.append(doc)

        print str(ti)
