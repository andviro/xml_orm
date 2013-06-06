#!/usr/bin/env python
#-*- coding: utf-8 -*-
from xml_orm.schemas.stat import ContainerStat
from xml_orm.schemas.auto import autoload
from uuid import uuid4
import os


def test_create():
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
    stat.receiver_sys = stat.Receiver_sys(uid='2AE', type=u'оператор')
    doctypes = [u'отчет', u'отчетИзвещение', u'протокол', u'протоколИзвещение', ]
    for n in range(3):
        stat.add_file(filename='some{0}.xml'.format(n), doc_type=doctypes[n],
                      content_type='xml', content='test content {0}'.format(n),
                      signature='test sign content {0}'.format(n),
                      sig_role=u'респондент')
    assert 0
    return stat


def test_main_doc():
    stat = test_create()
    assert (stat.main_document.orig_filename == 'some0.xml'
            and stat.main_document.type == u'отчет')


def test_save_load():
    stat = test_create()
    stat.save()
    print repr(stat)
    newstat = autoload(stat.package)
    assert isinstance(newstat, ContainerStat)
    os.unlink(stat.package)
