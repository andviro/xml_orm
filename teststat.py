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
    stat.doc_type = 'отчетСтат'
    stat.transaction = 'протоколИзвещение'
    stat.sender = stat.Sender(uid=uuid4().hex, type='респондент', name='рога и копыта')
    stat.receiver = stat.Receiver(uid=uuid4().hex, type='органФСГС')
    stat.sender_sys = stat.Sender_sys(uid='2AE', type='оператор')
    stat.receiver_sys = stat.Receiver_sys(uid='2AE', type='оператор')
    for n in range(3):
        stat.add_file(filename='some{0}.xml'.format(n), doc_type='отчет',
                      content_type='xml', content='test content {0}'.format(n),
                      signature='test sign content {0}'.format(n),
                      sig_role='респондент')


def teardown_module():
    os.unlink(stat.package)


def test_save_load():
    global stat
    stat.save()
    newstat = autoload(stat.package)
    assert isinstance(newstat, ContainerStat)
