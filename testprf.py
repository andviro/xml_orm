#!/usr/bin/env python
#-*- coding: utf-8 -*-
from containers.pfr import ContainerPFR, PFRSender, PFRReceiver, PFRDocument, SKZI
from containers.fns import SOS, Signature, Content
from uuid import uuid4


def main():
    # Создание контейнера "с нуля"
    # в параметрах конструкторы можно передавать начальные значения полей
    # для непереданных полей присваиваются значения по умолчанию
    # неприсвоенные поля без умолчаний бросят исключение при попытке вызвать
    # .save() или преобразовать контейнер в XML.
    ti = ContainerPFR(uid=uuid4().hex)
    ti.sender = PFRSender(uid=uuid4().hex)
    ti.skzi = SKZI(uid=uuid4().hex)
    ti.receiver = PFRReceiver(uid=uuid4().hex)
    ti.sos = SOS(uid=u'2AE')
    for n in range(3):
        doc = PFRDocument()
        doc.uid = uuid4().hex
        doc.orig_filename = doc.uid + '.xml'
        doc.content = Content(filename=(doc.uid + '.bin'))
        # Добавление дескриптора документа к дескриптору контейнера
        ti.files.append(doc)
        # Добавление собственно файла к содержимому контейнера
        ti.add_file(doc.content.filename, 'test document content')
        for k in range(2):
            sig = Signature(filename=(uuid4().hex + '.bin'))
            # Добавление дескриптора подписи к дескриптору документа
            doc.signature.append(sig)
            # Добавление файла подписи к содержимому контейнера
            ti.add_file(sig.filename, 'test signature content')
    print ti

if __name__ == "__main__":
    main()
