#!/usr/bin/env python
#-*- coding: utf-8 -*-
import core
import sys
from uuid import uuid4


class Sender(core.Schema):
    u''' XML-дескриптор отправителя
    '''
    # Идентификатор абонента или спецоператора
    uid = core.SimpleField(u'@идентификаторСубъекта')

    # Тип отправителя, значение по умолчанию устанавливается на основе
    # идентификатора отправителя
    type = core.SimpleField(u'@типСубъекта', getter='get_type',
                            setter='set_type')

    def get_type(self):
        if not hasattr(self, '__type'):
            if len(self.uid) == 3:
                self.__type = u'спецоператор'
            elif len(self.uid) == 4:
                self.__type = u'налоговыйОрган'
            else:
                self.__type = u'абонент'
        return self.__type

    def set_type(self, value):
        self.__type = value

    class Meta:
        root = u'отправитель'


class SOS(Sender):
    u"""Дескриптор спецоператора, отличается от отправителя только тегом. """

    class Meta:
        root = u'спецоператор'


class Receiver(Sender):
    u"""Дескриптор получателя, отличается от отправителя только тегом. """

    class Meta:
        root = u'получатель'


class Content(core.Schema):
    u"""Дескриптор содержимого документа."""

    # Имя файла в архиве
    filename = core.SimpleField(u'@имяФайла')

    class Meta:
        root = u'содержимое'


class Signature(Content):
    u"""Дескриптор подписи документа. Отличается от содержимого наличием поля 'role' """

    role = core.SimpleField(u'@роль', default=u'абонент')

    class Meta:
        root = u'подпись'


class Document(core.Schema):
    u"""Дескриптор документа.

    """
    # атрибуты документа
    type_code = core.CharField(u'@кодТипаДокумента', max_length=2, default=u'01')
    type = core.SimpleField(u'@типДокумента', default=u'счетфактура')
    content_type = core.SimpleField(u'@типСодержимого', default=u'xml')
    compressed = core.BooleanField(u'@сжат', default=False)
    encrypted = core.BooleanField(u'@зашифрован', default=False)
    sign_required = core.BooleanField(u'@ОжидаетсяПодписьПолучателя', minOccurs=0)
    uid = core.SimpleField(u'@идентификаторДокумента')
    orig_filename = core.SimpleField(u'@исходноеИмяФайла')

    # содержимое
    content = core.ComplexField(Content)
    # подписи, представляются в виде списка элементов типа Signature
    signature = core.ComplexField(Signature, maxOccurs='unbounded')

    class Meta:
        root = u'документ'


class TransInfo(core.Schema):
    u""" XML-дескриптор контейнера.

    """
    version = core.SimpleField(u'@версияФормата', default=u"ФНС:1.0")
    doc_type = core.SimpleField(u'@типДокументооборота', default=u"СчетФактура")
    doc_code = core.CharField(u'@кодТипаДокументооборота', max_length=2, default=u"20")
    doc_id = core.SimpleField(u'@идентификаторДокументооборота')
    trans_type = core.SimpleField(u'@типТранзакции', default=u'СчетФактураПродавец')
    trans_code = core.CharField(u'@кодТипаТранзакции', max_length=2, default=u'01')
    soft_version = core.SimpleField(u'@ВерсПрог', default=u'АстралОтчет 1.0')
    sender = core.ComplexField(Sender)
    sos = core.ComplexField(SOS)
    receiver = core.ComplexField(Receiver)
    extra = core.RawField(u'ДопСв', minOccurs=0)
    # документы представляются в виде списка
    document = core.ComplexField(Document, maxOccurs='unbounded')

    class Meta:
        root = u'ТрансИнф'


class ContainerFNS(core.Zipped, TransInfo):
    """Docstring for ContainerFNS """

    def __init__(self, *args, **nargs):
        u''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        self.uid = uuid4().hex
        super(ContainerFNS, self).__init__(*args, **nargs)

    class Meta:
        # имя файла с дескриптором в архиве. При наследовании может быть
        # изменено.
        entry = 'packageDescription.xml'

        # кодировка в которой сохранится XML
        encoding = 'cp1251'

        # управление форматированием сохраняемого XML
        pretty_print = True

        package = ('FNS_{self.sender.uid}_{self.receiver.uid}_{self.uid}'
                   '_{self.doc_code}_{self.trans_code}_{self.document[0].type_code}.zip')


if __name__ == '__main__':
    # Создание контейнера "с нуля"
    # в параметрах конструкторы можно передавать начальные значения полей
    # для непереданных полей присваиваются значения по умолчанию
    # неприсвоенные поля без умолчаний бросят исключение при попытке вызвать
    # .save() или преобразовать контейнер в XML.
    ti = ContainerFNS(doc_id=uuid4().hex)
    ti.sender = Sender(uid=uuid4().hex)
    ti.receiver = Receiver(uid=uuid4().hex)
    ti.sos = SOS(uid=u'2AE')
    for n in range(3):
        doc = Document()
        doc.uid = uuid4().hex
        doc.orig_filename = doc.uid + '.xml'
        doc.content = Content(filename=(doc.uid + '.bin'))
        # Добавление дескриптора документа к дескриптору контейнера
        ti.document.append(doc)
        # Добавление собственно файла к содержимому контейнера
        ti.add_file(doc.content.filename, 'test document content')
        for k in range(2):
            sig = Signature(filename=(uuid4().hex + '.bin'))
            # Добавление дескриптора подписи к дескриптору документа
            doc.signature.append(sig)
            # Добавление файла подписи к содержимому контейнера
            ti.add_file(sig.filename, 'test signature content')

    # сохранение сработает, только если контейнер сформирован корректно
    try:
        ti.save()
    except:
        print sys.exc_info()[:2]
    else:
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
