#!/usr/bin/env python
#-*- coding: utf-8 -*-

from uuid import uuid4
from schemas.fns import ContainerFNS

# Создание контейнера "с нуля"
# в параметрах конструктору можно передавать начальные значения полей
# для непереданных полей присваиваются значения по умолчанию
# неприсвоенные поля без умолчаний бросят исключение при попытке вызвать
# .save() или преобразовать контейнер в XML.
ti = ContainerFNS(uid=uuid4().hex)
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

# сохранение сработает, только если контейнер сформирован корректно
ti.save()
print ti.package
# загрузка контейнера из файла производится по имени, либо из байтовой
# строки содержимого, либо из открытого файлового объекта
with ContainerFNS.load(ti.package) as newti:
    # добавления и изменения структуры отразятся на сохраненном
    # содержимом архива
    newti.add_file('lalalala', 'lalalala')
    # если не изменить поле 'package', файл архива перезапишет исходный
    # загруженный файл. Для вновь созданных контейнеров это поле
    # пустое, и имя пакета формируется автоматически.
    newti.package = 'some_other.zip'
    # выход из контекста сохраняет архив
