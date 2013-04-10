#!/usr/bin/env python
#-*- coding: utf-8 -*-

from uuid import uuid4
from containers.fns import ContainerFNS

# —оздание контейнера "с нул€"
# в параметрах конструктору можно передавать начальные значени€ полей
# дл€ непереданных полей присваиваютс€ значени€ по умолчанию
# неприсвоенные пол€ без умолчаний брос€т исключение при попытке вызвать
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
    # ƒобавление дескриптора документа к дескриптору контейнера
    ti.doc.append(doc)
    # ƒобавление собственно файла к содержимому контейнера
    ti.add_file(doc.content.filename, 'test document content')
    for k in range(2):
        sig = doc.Signature(filename=(uuid4().hex + '.bin'))
        # ƒобавление дескриптора подписи к дескриптору документа
        doc.signature.append(sig)
        # ƒобавление файла подписи к содержимому контейнера
        ti.add_file(sig.filename, 'test signature content')

# сохранение сработает, только если контейнер сформирован корректно
ti.save()
print ti.package
# загрузка контейнера из файла производитс€ по имени, либо из байтовой
# строки содержимого, либо из открытого файлового объекта
with ContainerFNS.load(ti.package) as newti:
    # добавлени€ и изменени€ структуры отраз€тс€ на сохраненном
    # содержимом архива
    newti.add_file('lalalala', 'lalalala')
    # если не изменить поле 'package', файл архива перезапишет исходный
    # загруженный файл. ƒл€ вновь созданных контейнеров это поле
    # пустое, и им€ пакета формируетс€ автоматически.
    newti.package = 'some_other.zip'
    # выход из контекста сохран€ет архив
