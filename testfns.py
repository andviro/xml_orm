#!/usr/bin/env python
#-*- coding: utf-8 -*-

from uuid import uuid4
from xml_orm.schemas.fns import ContainerFNS
from xml_orm.schemas.auto import autoload
import os

ti = None
extra_package = ''


def setup_module():
    global ti
    # Создание контейнера "с нуля"
    # в параметрах конструктору можно передавать начальные значения полей
    # для непереданных полей присваиваются значения по умолчанию
    # неприсвоенные поля без умолчаний бросят исключение при попытке вызвать
    # .save() или преобразовать контейнер в XML.
    with ContainerFNS(uid=uuid4().hex) as ti:
        # сохранение сработает, только если контейнер сформирован корректно
        ti.sender = ContainerFNS.Sender(uid=uuid4().hex)
        ti.receiver = ti.Receiver(uid=uuid4().hex)
        ti.sos = ti.Sos(uid=u'2AE')
        for n in range(3):
            uid = uuid4().hex
            doc = ti.Doc(
                uid=uid,
                orig_filename=uid + '.xml',
                content=ti.Doc.Content(filename=(uid + '.bin')))
            print unicode(doc)
            # Добавление дескриптора документа к дескриптору контейнера
            ti.doc.append(doc)
            # Добавление собственно файла к содержимому контейнера
            ti.add_file(doc.content.filename, 'test document content')
            for k in range(2):
                sig = doc.Signature(filename=(uuid4().hex + '.bin'))
                # Добавление дескриптора подписи к дескриптору документа
                doc.signature.append(sig)
                # Добавление файла подписи к содержимому контейнера
                ti.add_file(sig.filename, 'test signature content')


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
        newti.add_file('lalalala', 'lalalala')
        # если не изменить поле 'package', файл архива перезапишет исходный
        # загруженный файл. Для вновь созданных контейнеров это поле
        # пустое, и имя пакета формируется автоматически.
        newti.package = extra_package = '{0}.zip'.format(uuid4().hex)
        # выход из контекста сохраняет архив
    assert os.path.isfile(extra_package)
