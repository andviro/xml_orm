#!/usr/bin/env python
#-*- coding: utf-8 -*-

from ..core import Schema
from ..util import Zipped
from ..fields import *
from .util import ContainerUtil
from uuid import uuid4


'''
_edo_type_map = {'код документооборота': ('тип документооборота', {
                  'код транзакции': 'тип транзакции',
                  })
                 }

'''

_edo_type_map = {
    '1': ('письмоРеспондент', {
        '1': 'письмо',
        '2': 'извещение',
    }),
    '2': ('письмоОрганФСГС', {
        '1': 'письмо',
        '2': 'подтверждение',
        '3': 'извещение',
    }),
    '3': ('рассылка', {
        '1': 'рассылка',
        '2': 'подтверждение',
    }),
    '4': ('отчетСтат', {
        '1': 'отчет',
        '2': 'отчетИзвещение',
        '3': 'протокол',
        '4': 'протоколИзвещение',
    }),
    '5': ('ОшибкаОбработкиПакета', {
        '1': 'уведомлениеОбОшибке',
    })
}

_reverse_edo_map = dict(
    (v[0], (k, dict((v, k) for (k, v) in v[1].items()))) for (k, v) in _edo_type_map.items())


class StatSender(Schema):
    class Meta:
        root = 'отправитель'

    uid = SimpleField('@идентификаторСубъекта')
    type = SimpleField('@типСубъекта')
    name = SimpleField('@названиеОрганизации', minOccurs=0)


class StatSystem(Schema):
    class Meta:
        root = 'системаОтправителя'

    uid = SimpleField('@идентификаторСубъекта')
    type = SimpleField('@типСубъекта')


class StatReceiver(StatSystem):
    class Meta:
        root = 'получатель'


class StatDocument(Schema):
    class Meta:
        root = 'документ'

    #содержимое
    content = ComplexField('содержимое',
                           minOccurs=0,

                           filename=SimpleField('@имяФайла')
                           )
    #подпись
    signature = ComplexField('подпись',
                             minOccurs=0,
                             maxOccurs='unbounded',

                             role=SimpleField('@роль'),
                             filename=SimpleField('@имяФайла'),
                             )
    type = SimpleField('@типДокумента')
    content_type = SimpleField('@типСодержимого')
    compressed = BooleanField('@сжат')
    encrypted = BooleanField('@зашифрован')
    uid = SimpleField('@идентификаторДокумента')

    def __init__(self, *args, **nargs):
        ''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        super(StatDocument, self).__init__(*args, **nargs)


class StatInfo(Schema):
    class Meta:
        root = 'пакет'

    version = SimpleField('@версияФормата', default='Стат:1.0')
    uid = SimpleField('@идентификаторДокументооборота')
    doc_type = SimpleField('@типДокументооборота')
    transaction = SimpleField('@типТранзакции')

    #отправитель
    sender = ComplexField(StatSender)
    sender_sys = ComplexField('системаОтправителя',
                              minOccurs=0,
                              uid=SimpleField('@идентификаторСубъекта'),
                              type=SimpleField('@типСубъекта'),
                              )
    #получатель
    receiver = ComplexField(StatReceiver)
    receiver_sys = ComplexField('системаПолучателя',
                                minOccurs=0,
                                uid=SimpleField('@идентификаторСубъекта'),
                                type=SimpleField('@типСубъекта'),
                                )
    extra = RawField('расширения', minOccurs=0)
    #документ
    doc = ComplexField(StatDocument, minOccurs=0, maxOccurs='unbounded')


class ContainerStat(Zipped, ContainerUtil, StatInfo):
    """Docstring for ContainerStat """

    protocol = 4

    def __init__(self, *args, **nargs):
        ''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        self.file_uid = uuid4().hex
        super(ContainerStat, self).__init__(*args, **nargs)

    @property
    def doc_code(self):
        '''
        Автоматически вычисляемый код типа документооборота
        '''
        doc_code, _ = _reverse_edo_map.get(self.doc_type, None)
        return doc_code

    @property
    def trans_code(self):
        '''
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
