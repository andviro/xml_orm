#!/usr/bin/env python
#-*- coding: utf-8 -*-

from ..core import Schema
from ..util import Zipped
from ..fields import *
from .fns import Sender
from .util import ContainerUtil
from uuid import uuid4

u'''
_edo_type_map = {'код документооборота': ('тип документооборота', {
                  'код транзакции': 'тип транзакции',
                  })
                 }

'''
_edo_type_map = {
    '1': (u'СведенияПФР', {
        '1': u"сведения",
        '2': u"подтверждениеПолучения",
        '3': u"протокол",
        '4': u"протоколКвитанция",
    }),
    '2': (u'УточнениеПлатежей', {
        '1': u"запрос",
        '2': u"запросКвитанция",
        '3': u"ответ",
        '4': u"ответКвитанция",
    }),
    '3': (u'Декларация', {
        '1': u"декларация",
        '2': u"декларацияКвитанция",
    }),
    '4': (u'Письмо', {
        '1': u"письмо",
        '2': u"письмоКвитанция",
    }),
    '5': (u"ОшибкаОбработкиПакета", {
        '1': u"уведомлениеОбОшибке",
    }),
    '6': (u"РегистрацияСертификатов", {
        '1': u"Регистрация",
        '2': u"регистрацияКвитанция",
    }),
    '7': (u"ЗапросыФССП", {
        '1': u"запрос",
        '2': u"подтверждениеПолучения",
        '3': u"ответ",
        '4': u"протоколКвитанция"
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
                self.__type = u"АбонентСЭД"
            elif len(t) == 2:
                self.__type = u"ОрганПФР"
            else:
                self.__type = u"Провайдер"
        return self.__type


class PFRReceiver(PFRSender):
    u"""Дескриптор получателя, отличается от отправителя только тегом. """

    class Meta:
        root = u'получатель'


class PFRSystemSender(PFRSender):
    """Дескриптор получателя, отличается от отправителя только тегом. """

    class Meta:
        root = u'системаОтправителя'


class PFRSystemReceiver(PFRSender):
    u"""Дескриптор получателя, отличается от отправителя только тегом. """

    class Meta:
        root = u'системаПолучателя'


class PFRDocument(Schema):
    u"""Дескриптор документа.

    """
    # атрибуты документа
    type = SimpleField(u'@типДокумента')
    content_type = SimpleField(u'@типСодержимого')
    compressed = BooleanField(u'@сжат')
    encrypted = BooleanField(u'@зашифрован')
    sign_required = BooleanField(u'@ОжидаетсяПодписьПолучателя', minOccurs=0)
    uid = SimpleField(u'@идентификаторДокумента')

    content = ComplexField(u'содержимое',
                           minOccurs=0,

                           filename=SimpleField(u'@имяФайла')
                           )
    # подписи, представляются в виде списка элементов типа Signature
    signatures = ComplexField(u'подпись',
                              minOccurs=0,
                              maxOccurs='unbounded',

                              role=SimpleField(u'@роль'),
                              filename=SimpleField(u'@имяФайла'),
                              )

    class Meta:
        root = u'документ'

    def __init__(self, *args, **nargs):
        u''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        super(PFRDocument, self).__init__(*args, **nargs)


class SKZI(Schema):
    u"""Дескриптор документа.

    """
    # атрибуты документа
    type = SimpleField(u'@типСКЗИ')

    class Meta:
        root = u'СКЗИ'


class PFRInfo(Schema):
    # атрибуты
    version = SimpleField(u'@версияФормата', default="1.2")
    doc_type = SimpleField(u'@типДокументооборота')
    transaction = SimpleField(u'@типТранзакции')
    uid = SimpleField(u'@идентификаторДокументооборота')
    date = SimpleField(u'@датаВремяПоступления', minOccurs=0)
    # элементы
    skzi = ComplexField(SKZI)
    sender = ComplexField(PFRSender)
    sender_sys = ComplexField(PFRSystemSender, minOccurs=0)
    receiver_sys = ComplexField(PFRSystemReceiver, minOccurs=0)
    receiver = ComplexField(PFRReceiver)
    extra = RawField(u'расширения', minOccurs=0)
    docs = ComplexField(PFRDocument, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        root = u'пакет'
        pretty_print = True
        encoding = 'utf-8'


class ContainerPFR(Zipped, ContainerUtil, PFRInfo):

    protocol = 2

    def __init__(self, *args, **nargs):
        u''' Инициализация полей, которые не загружаются/сохраняются из
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
    def doc_code(self):
        u'''
        Автоматически вычисляемый код типа документооборота
        '''
        doc_code, _ = _reverse_edo_map.get(self.doc_type, None)
        return doc_code

    @property
    def is_positive(self):
        """@todo: Docstring for is_positive
        :returns: @todo

        """
        assert self.transaction == u'протокол', 'wrong transaction type'
        return any(item.type.startswith(u'пачка') or
                   item.type.startswith(u'реестрДСВ') for item in self.files)
