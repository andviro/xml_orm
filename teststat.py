#!/usr/bin/env python
#-*- coding: utf-8 -*-
from xml_orm.schemas.stat import ContainerStat
from xml_orm.schemas.auto import autoload
from uuid import uuid4
import os

stat = None


def setup_module():
    global stat
    # Создание контейнера "с нуля"
    # в параметрах конструкторы можно передавать начальные значения полей
    # для непереданных полей присваиваются значения по умолчанию
    # неприсвоенные поля без умолчаний бросят исключение при попытке вызвать
    # .save() или преобразовать контейнер в XML.
    stat = ContainerStat(uid=uuid4().hex)
    stat.doc_type = u'отчетСтат'
    stat.transaction = u'протоколИзвещение'
    stat.sender = stat.Sender(uid=uuid4().hex, type=u'респондент', name=u'рога и копыта')
    stat.receiver = stat.Receiver(uid=uuid4().hex, type=u'органФСГС')
    stat.sender_sys = stat.Sender_sys(uid=u'2AE', type=u'оператор')
    stat.receiver_sys = stat.Receiver_sys(uid=u'2AE', type=u'оператор')
    for n in range(3):
        doc = stat.Doc()
        doc.uid = uuid4().hex
        doc.orig_filename = doc.uid + '.xml'
        doc.content = doc.Content(filename=(doc.uid + '.bin'))
        doc.compressed = doc.encrypted = True
        doc.content_type = u'xml'
        doc.type = u'отчет'
        # Добавление дескриптора документа к дескриптору контейнера
        stat.doc.append(doc)
        # Добавление собственно файла к содержимому контейнера
        stat.add_file(doc.content.filename, 'test document content')
        for k in range(2):
            sig = doc.Signature(filename=(uuid4().hex + '.bin'),
                                role=u'респондент')
            # Добавление дескриптора подписи к дескриптору документа
            doc.signature.append(sig)
            # Добавление файла подписи к содержимому контейнера
            stat.add_file(sig.filename, 'test signature content')


def teardown_module():
    os.unlink(stat.package)


def test_save_load():
    global stat
    stat.save()
    newstat = autoload(stat.package)
    assert isinstance(newstat, ContainerStat)
