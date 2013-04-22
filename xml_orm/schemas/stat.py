#!/usr/bin/env python
#-*- coding: utf-8 -*-

from ..core import Schema
from ..util import Zipped
from ..fields import *
from .util import ContainerUtil
from uuid import uuid4


u'''
_edo_type_map = {'код документооборота': ('тип документооборота', {
                  'код транзакции': 'тип транзакции',
                  })
                 }

'''

_edo_type_map = {
    '1': (u'письмоРеспондент', {
        '1': u'письмо',
        '2': u'извещение',
    }),
    '2': (u'письмоОрганФСГС', {
        '1': u'письмо',
        '2': u'подтверждение',
        '3': u'извещение',
    }),
    '3': (u'рассылка', {
        '1': u'рассылка',
        '2': u'подтверждение',
    }),
    '4': (u'отчетСтат', {
        '1': u'отчет',
        '2': u'отчетИзвещение',
        '3': u'протокол',
        '4': u'протоколИзвещение',
    }),
    '5': (u'ОшибкаОбработкиПакета', {
        '1': u'уведомлениеОбОшибке',
    })
}

_reverse_edo_map = dict(
    (v[0], (k, dict((v, k) for (k, v) in v[1].items()))) for (k, v) in _edo_type_map.items())


class StatSender(Schema):
    class Meta:
        root = u'отправитель'

    uid = SimpleField(u'@идентификаторСубъекта')
    type = SimpleField(u'@типСубъекта')
    name = SimpleField(u'@названиеОрганизации', minOccurs=0)


class StatSystem(Schema):
    class Meta:
        root = u'системаОтправителя'

    uid = SimpleField(u'@идентификаторСубъекта')
    type = SimpleField(u'@типСубъекта')


class StatReceiver(StatSystem):
    class Meta:
        root = u'получатель'


class StatDocument(Schema):
    class Meta:
        root = u'документ'

    #содержимое
    content = ComplexField(u'содержимое',
                           minOccurs=0,

                           filename=SimpleField(u'@имяФайла')
                           )
    #подпись
    signature = ComplexField(u'подпись',
                             minOccurs=0,
                             maxOccurs='unbounded',

                             role=SimpleField(u'@роль'),
                             filename=SimpleField(u'@имяФайла'),
                             )
    type = SimpleField(u'@типДокумента')
    content_type = SimpleField(u'@типСодержимого')
    compressed = BooleanField(u'@сжат')
    encrypted = BooleanField(u'@зашифрован')
    uid = SimpleField(u'@идентификаторДокумента')

    def __init__(self, *args, **nargs):
        u''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        super(StatDocument, self).__init__(*args, **nargs)


class StatInfo(Schema):
    class Meta:
        root = u'пакет'

    version = SimpleField(u'@версияФормата', default=u'Стат:1.0')
    uid = SimpleField(u'@идентификаторДокументооборота')
    doc_type = SimpleField(u'@типДокументооборота')
    transaction = SimpleField(u'@типТранзакции')

    #отправитель
    sender = ComplexField(StatSender)
    sender_sys = ComplexField(u'системаОтправителя',
                              minOccurs=0,
                              uid=SimpleField(u'@идентификаторСубъекта'),
                              type=SimpleField(u'@типСубъекта'),
                              )
    #получатель
    receiver = ComplexField(StatReceiver)
    receiver_sys = ComplexField(u'системаПолучателя',
                                minOccurs=0,
                                uid=SimpleField(u'@идентификаторСубъекта'),
                                type=SimpleField(u'@типСубъекта'),
                                )
    extra = RawField(u'расширения', minOccurs=0)
    #документ
    doc = ComplexField(StatDocument, minOccurs=0, maxOccurs='unbounded')


class ContainerStat(Zipped, ContainerUtil, StatInfo):
    u"""Docstring for ContainerStat """

    protocol = 4

    def __init__(self, *args, **nargs):
        u''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        self.file_uid = uuid4().hex
        super(ContainerStat, self).__init__(*args, **nargs)

    @property
    def doc_code(self):
        u'''
        Автоматически вычисляемый код типа документооборота
        '''
        doc_code, _ = _reverse_edo_map.get(self.doc_type, None)
        return doc_code

    @property
    def trans_code(self):
        u'''
        Автоматически вычисляемый код типа транзакции
        '''
        _, tr_map = _reverse_edo_map.get(self.doc_type, (0, []))
        return dict(tr_map).get(self.transaction, 0)

    class Meta:
        # имя файла с дескриптором в архиве. При наследовании может быть
        # изменено.
        entry = 'packageDescription.xml'

        package = 'STAT_{self.sender.uid}_{self.receiver.uid}_{self.file_uid}_{self.doc_code}_{self.trans_code}.zip'

        # кодировка в которой сохранится XML
        encoding = 'cp1251'

        # управление форматированием сохраняемого XML
        pretty_print = True
