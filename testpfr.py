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
                       doc_type='СведенияПФР',
                       transaction="сведения",)
    pfr.sender = pfr.Sender(uid='123-456-789012')
    pfr.skzi = pfr.Skzi(uid=uuid4().hex, type='Крипто-Про')
    pfr.receiver = pfr.Receiver(uid='123-534')
    pfr.sender_sys = pfr.Sender_sys(uid='2AE')
    for n in range(3):
        pfr.add_file(filename='some{0}.xml'.format(n), doc_type='протокол',
                     content_type='xml', content='test content {0}'.format(n),
                     signature='test sign content {0}'.format(n),
                     sig_role='провайдер')


def teardown_module():
    os.unlink(pfr.package)


def test_save_load():
    global pfr
    pfr.save()
    newpfr = autoload(pfr.package)
    assert isinstance(newpfr, ContainerPFR)
