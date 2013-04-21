#!/usr/bin/env python
#-*- coding: utf-8 -*-

from .. import core
from .fns import Sender
from .util import ContainerUtil
from uuid import uuid4

'''
_edo_type_map = {'код документооборота': ('тип документооборота', {
                  'код транзакции': 'тип транзакции',
                  })
                 }

'''
_edo_type_map = {
    '1': ('СведенияПФР', {
        '1': "сведения",
        '2': "подтверждениеПолучения",
        '3': "протокол",
        '4': "протоколКвитанция",
    }),
    '2': ('УточнениеПлатежей', {
        '1': "запрос",
        '2': "запросКвитанция",
        '3': "ответ",
        '4': "ответКвитанция",
    }),
    '3': ('Декларация', {
        '1': "декларация",
        '2': "декларацияКвитанция",
    }),
    '4': ('Письмо', {
        '1': "письмо",
        '2': "письмоКвитанция",
    }),
    '5': ("ОшибкаОбработкиПакета", {
        '1': "уведомлениеОбОшибке",
    }),
    '6': ("РегистрацияСертификатов", {
        '1': "Регистрация",
        '2': "регистрацияКвитанция",
    }),
    '7': ("ЗапросыФССП", {
        '1': "запрос",
        '2': "подтверждениеПолучения",
        '3': "ответ",
        '4': "протоколКвитанция"
    }),
}
_reverse_edo_map = dict(
    (v[0], (k, dict((v, k) for (k, v) in v[1].items()))) for (k, v) in _edo_type_map.items())


class PFRSender(Sender):
    # TODO
    def get_type(self):
        if not hasattr(self, '__type'):
            t = self.uid.split('-')
            if len(t) == 3:
                self.__type = "АбонентСЭД"
            elif len(t) == 2:
                self.__type = "ОрганПФР"
            else:
                self.__type = "Провайдер"
        return self.__type


class PFRReceiver(PFRSender):
    """Дескриптор получателя, отличается от отправителя только тегом. """

    class Meta:
        root = 'получатель'


class PFRSystemSender(PFRSender):
    """Дескриптор получателя, отличается от отправителя только тегом. """

    class Meta:
        root = 'системаОтправителя'


class PFRSystemReceiver(PFRSender):
    """Дескриптор получателя, отличается от отправителя только тегом. """

    class Meta:
        root = 'системаПолучателя'


class PFRDocument(core.Schema):
    """Дескриптор документа.

    """
    # атрибуты документа
    type = core.SimpleField('@типДокумента')
    content_type = core.SimpleField('@типСодержимого')
    compressed = core.BooleanField('@сжат')
    encrypted = core.BooleanField('@зашифрован')
    sign_required = core.BooleanField('@ОжидаетсяПодписьПолучателя', minOccurs=0)
    uid = core.SimpleField('@идентификаторДокумента')

    content = core.ComplexField('содержимое',
                                minOccurs=0,

                                filename=core.SimpleField('@имяФайла')
                                )
    # подписи, представляются в виде списка элементов типа Signature
    signature = core.ComplexField('подпись',
                                  minOccurs=0,
                                  maxOccurs='unbounded',

                                  role=core.SimpleField('@роль'),
                                  filename=core.SimpleField('@имяФайла'),
                                  )

    class Meta:
        root = 'документ'

    def __init__(self, *args, **nargs):
        ''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        super(PFRDocument, self).__init__(*args, **nargs)


class SKZI(core.Schema):
    """Дескриптор документа.

    """
    # атрибуты документа
    type = core.SimpleField('@типСКЗИ')

    class Meta:
        root = 'СКЗИ'


class PFRInfo(core.Schema):
    # атрибуты
    version = core.SimpleField('@версияФормата', default="1.2")
    doc_type = core.SimpleField('@типДокументооборота')
    transaction = core.SimpleField('@типТранзакции')
    uid = core.SimpleField('@идентификаторДокументооборота')
    date = core.SimpleField('@датаВремяПоступления', minOccurs=0)
    # элементы
    skzi = core.ComplexField(SKZI)
    sender = core.ComplexField(PFRSender)
    sender_sys = core.ComplexField(PFRSystemSender, minOccurs=0)
    receiver_sys = core.ComplexField(PFRSystemReceiver, minOccurs=0)
    receiver = core.ComplexField(PFRReceiver)
    extra = core.RawField('расширения', minOccurs=0)
    doc = core.ComplexField(PFRDocument, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        root = 'пакет'
        pretty_print = True
        encoding = 'utf-8'


class ContainerPFR(core.Zipped, ContainerUtil, PFRInfo):

    protocol = 2

    def __init__(self, *args, **nargs):
        ''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        self.file_uid = uuid4().hex
        super(ContainerPFR, self).__init__(*args, **nargs)

    class Meta:
        # имя файла с дескриптором в архиве. При наследовании может быть
        # изменено.
        entry = 'packageDescription.xml'

        package = '{self.sender.uid}_{self.receiver.uid}_{self.file_uid}.zip'

        # кодировка в которой сохранится XML
        encoding = 'cp1251'

        # управление форматированием сохраняемого XML
        pretty_print = True

    @property
    def is_positive(self):
        """@todo: Docstring for is_positive
        :returns: @todo

        """
        assert self.transaction == 'протокол', 'wrong transaction type'
        return any(item.type.startswith('пачка') or
                   item.type.startswith('реестрДСВ') for item in self.files)
