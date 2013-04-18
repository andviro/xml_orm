#!/usr/bin/env python
#-*- coding: utf-8 -*-
from xml_orm.schemas.pfr import ContainerPFR
from xml_orm.schemas.auto import autoload
from uuid import uuid4
import os

pfr = None


def setup_module():
    global pfr
    # Создание контейнера "с нуля"
    # в параметрах конструкторы можно передавать начальные значения полей
    # для непереданных полей присваиваются значения по умолчанию
    # неприсвоенные поля без умолчаний бросят исключение при попытке вызвать
    # .save() или преобразовать контейнер в XML.
    pfr = ContainerPFR(uid=uuid4().hex,
                       doc_type=u'СведенияПФР',
                       transaction=u"сведения",)
    pfr.sender = pfr.Sender(uid='123-456-789012')
    pfr.skzi = pfr.Skzi(uid=uuid4().hex, type='Крипто-Про')
    pfr.receiver = pfr.Receiver(uid='123-534')
    pfr.sos = pfr.Sos(uid=u'2AE')
    for n in range(3):
        doc = pfr.Doc()
        doc.uid = uuid4().hex
        doc.orig_filename = doc.uid + '.xml'
        doc.type = u'протокол'
        doc.content_type = u'plain866'
        doc.compressed = False
        doc.encrypted = False
        doc.content = doc.Content(filename=(doc.uid + '.bin'))
        # Добавление дескриптора документа к дескриптору контейнера
        pfr.doc.append(doc)
        # Добавление собственно файла к содержимому контейнера
        pfr.add_file(doc.content.filename, 'test document content')
        for k in range(2):
            sig = doc.Signature(filename=(uuid4().hex + '.bin'), role=u'провайдер')
            # Добавление дескриптора подписи к дескриптору документа
            doc.signature.append(sig)
            # Добавление файла подписи к содержимому контейнера
            pfr.add_file(sig.filename, 'test signature content')


def teardown_module():
    os.unlink(pfr.package)


def test_save_load():
    global pfr
    pfr.save()
    newpfr = autoload(pfr.package)
    assert isinstance(newpfr, ContainerPFR)
