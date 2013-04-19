#!/usr/bin/env python
#-*- coding: utf-8 -*-

from uuid import uuid4
from xml_orm.schemas.fns import ContainerFNS
from xml_orm.schemas.auto import autoload
import os
from zipfile import ZipFile

ti = None
extra_package = ''


def setup_module():
    global ti
    # Создание контейнера "с нуля"
    # в параметрах конструктору можно передавать начальные значения полей
    # для непереданных полей присваиваются значения по умолчанию
    # неприсвоенные поля без умолчаний бросят исключение при попытке вызвать
    # .save() или преобразовать контейнер в XML.
    ti = ContainerFNS(uid=uuid4().hex,
                      doc_type=u'Декларация',
                      doc_code='01',
                      trans_code='01',
                      transaction=u"ДекларацияНП",
                      )
    ti.sender = ContainerFNS.Sender(uid=uuid4().hex)
    ti.receiver = ti.Receiver(uid=uuid4().hex)
    ti.sos = ti.Sos(uid=u'2AE')
    for n in range(3):
        ti.add_file(filename='some{0}.xml'.format(n), doc_type=u'описание',
                    content_type='xml', content='test content {0}'.format(n),
                    signature='test sign content {0}'.format(n),
                    sig_role=u'спецоператор')
    # сохранение сработает, только если контейнер сформирован корректно
    ti.save()


def teardown_module():
    global ti, extra_package
    os.unlink(ti.package)
    if os.path.isfile(extra_package):
        os.unlink(extra_package)


def test_autoload():
    global ti
    newti = autoload(ti.package)
    assert isinstance(newti, ContainerFNS)


def test_load():
    global ti, extra_package
    # загрузка контейнера из файла производится по имени, либо из байтовой
    # строки содержимого, либо из открытого файлового объекта
    with ContainerFNS.load(ti.package) as newti:
        # добавления и изменения структуры отразятся на сохраненном
        # содержимом архива
        newti.write('lalalala', 'lalalala')
        # если не изменить поле 'package', файл архива перезапишет исходный
        # загруженный файл. Для вновь созданных контейнеров это поле
        # пустое, и имя пакета формируется автоматически.
        newti.package = extra_package = '{0}.zip'.format(uuid4().hex)
        # выход из контекста сохраняет архив
    assert os.path.isfile(extra_package)
    assert 'lalalala' in ZipFile(extra_package).namelist()

setup_module()
