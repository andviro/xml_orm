#!/usr/bin/env python
#-*- coding: utf-8 -*-
from schemas.pfr import ContainerPFR
from schemas.auto import autoload
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
    pfr.skzi = pfr.Skzi(uid=uuid4().hex, type=u'Крипто-Про')
    pfr.receiver = pfr.Receiver(uid='123-534')
    pfr.sender_sys = pfr.Sender_sys(uid='2AE')
    dtypes = [u"сведения", u"подтверждениеПолучения", u"протокол", u"протоколКвитанция", ]
    for n in range(3):
        pfr.add_file(filename='some{0}.xml'.format(n), doc_type=dtypes[n],
                     content_type='xml', content='test content {0}'.format(n),
                     signature='test sign content {0}'.format(n),
                     sig_role=u'провайдер')


def teardown_module():
    os.unlink(pfr.package)


def test_main_doc():
    global pfr
    assert (pfr.main_document.orig_filename == 'some0.xml'
            and pfr.main_document.type == u'сведения')


def test_save_load():
    global pfr
    pfr.save()
    newpfr = autoload(pfr.package)
    assert isinstance(newpfr, ContainerPFR)
