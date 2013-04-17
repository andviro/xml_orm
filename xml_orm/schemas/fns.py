#!/usr/bin/env python
#-*- coding: utf-8 -*-
from uuid import uuid4
from .. import core


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
    content = core.ComplexField(Content, minOccurs=0)
    # подписи, представляются в виде списка элементов типа Signature
    signature = core.ComplexField(Signature, minOccurs=0, maxOccurs='unbounded')

    def __init__(self, *args, **nargs):
        u''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        super(Document, self).__init__(*args, **nargs)
        self.uid = uuid4().hex
        self.content = self.Content(filename=u'{0}.bin'.format(self.uid))

    class Meta:
        root = u'документ'


class TransInfo(core.Schema):
    u""" XML-дескриптор контейнера.

    """
    version = core.SimpleField(u'@версияФормата', default=u"ФНС:1.0")
    doc_type = core.SimpleField(u'@типДокументооборота', default=u"СчетФактура")
    doc_code = core.CharField(u'@кодТипаДокументооборота', max_length=2, default=u"20")
    uid = core.SimpleField(u'@идентификаторДокументооборота')
    transaction = core.SimpleField(u'@типТранзакции', default=u'СчетФактураПродавец')
    trans_code = core.CharField(u'@кодТипаТранзакции', max_length=2, default=u'01')
    soft_version = core.SimpleField(u'@ВерсПрог', default=u'АстралОтчет 1.0')
    sender = core.ComplexField(Sender)
    sos = core.ComplexField(SOS)
    receiver = core.ComplexField(Receiver)
    extra = core.RawField(u'ДопСв', minOccurs=0)
    # документы представляются в виде списка
    doc = core.ComplexField(Document, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        root = u'ТрансИнф'


class ContainerFNS(core.Zipped, TransInfo):
    """Docstring for ContainerFNS """

    protocol = 7

    def __init__(self, *args, **nargs):
        u''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        self.file_uid = uuid4().hex
        super(ContainerFNS, self).__init__(*args, **nargs)

    class Meta:
        # имя файла с дескриптором в архиве. При наследовании может быть
        # изменено.
        entry = 'packageDescription.xml'

        # кодировка в которой сохранится XML
        encoding = 'cp1251'

        # управление форматированием сохраняемого XML
        pretty_print = True

        package = ('FNS_{self.sender.uid}_{self.receiver.uid}_{self.file_uid}'
                   '_{self.doc_code}_{self.trans_code}_{self.doc[0].type_code}.zip')


class ContainerEDI(ContainerFNS):

    protocol = 20

    class Meta:
        package = ('EDI_{self.sender.uid}_{self.receiver.uid}_{self.file_uid}'
                   '_{self.doc_code}_{self.trans_code}_{self.doc[0].type_code}.zip')
