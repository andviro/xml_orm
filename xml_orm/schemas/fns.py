#!/usr/bin/env python
#-*- coding: utf-8 -*-
from uuid import uuid4
from ..core import Schema
from ..util import Zipped
from ..fields import *
from .util import ContainerUtil

'''
_edo_type_map = {'код документооборота': ('тип документооборота', {
                  'код транзакции': 'тип транзакции',
                  })
                 }

'''
_edo_type_map = {
    '01': ('Декларация', {
           '01': "ДекларацияНП",
           '02': "ИзвещениеДекларацияНО",
           '03': "ИзвещениеПодтверждениеНО",
           '04': "РезультатПриемаДекларацияНО",
           '05': "ИзвещениеРезультатПриемаСОС",
           '06': "ИзвещениеРезультатПриемаНП",
           '07': "РезультатОбработкиДекларацияНО",
           '08': "ИзвещениеРезультатОбработкиСОС",
           '09': "ИзвещениеРезультатОбработкиНП",
           '10': 'ПодтверждениеДекларацияНО',
           '11': 'ИзвещениеПодтверждениеНП',
           }),
    '02': ("ОбращениеНП", {
           '01': "ОбращениеНП",
           '02': "ИзвещениеОбращениеНО",
           '03': "ИзвещениеПодтверждениеНО",
           '04': "РезультатПриемаОбращениеНО",
           '05': "ИзвещениеРезультатПриемаСОС",
           '06': "ИзвещениеРезультатПриемаНП",
           '10': 'ПодтверждениеОбращениеНО',
           '11': 'ИзвещениеПодтверждениеНП',
           }),
    '03': ("ПисьмоНО", {
           '01': "ПисьмоНО",
           '02': "ПодтверждениеПисьмоСОС",
           '03': "ИзвещениеПисьмоНП",
           '04': "ИзвещениеПодтверждениеНО",
           }),
    '04': ("Рассылка", {
           '01': "РассылкаНО",
           '02': "ПодтверждениеРассылкаСОС",
           '03': "ИзвещениеПодтверждениеНО",
           }),
    '05': ("РассылкаГрупповая", {
           '01': "РассылкаНО",
           '02': "ПодтверждениеРассылкаСОС",
           '03': "ИзвещениеРассылкаНП",
           '04': "ИзвещениеПодтверждениеНО",
           }),
    '06': ("ИОН", {
           '01': "ЗапросНП",
           '02': "ИзвещениеЗапросНО",
           '03': "ИзвещениеПодтверждениеНО",
           '04': "РезультатПриемаЗапросНО",
           '05': "ИзвещениеРезультатПриемаСОС",
           '06': "ИзвещениеРезультатПриемаНП",
           '07': "РезультатОбработкиЗапросНО",
           '08': "ИзвещениеРезультатОбработкиСОС",
           '09': "ИзвещениеРезультатОбработкиНП",
           '10': 'ПодтверждениеЗапросНО',
           '11': 'ИзвещениеПодтверждениеНП',
           }),
    '07': ("ОшибкаОбработкиПакета", {
           '01': "СообщениеОбОшибке",
           }),
    '08': ("Сведения2НДФЛ", {
           '01': "Форма2НДФЛНП",
           '02': "ИзвещениеФорма2НДФЛНО",
           '03': "ИзвещениеПодтверждениеНО",
           '04': "РезультатПриемаФорма2НДФЛНО",
           '05': "ИзвещениеРезультатПриемаСОС",
           '06': "ИзвещениеРезультатПриемаНП",
           '10': 'ПодтверждениеФорма2НДФЛНО',
           '11': 'ИзвещениеПодтверждениеНП',
           }),
}

_reverse_edo_map = dict(
    (v[0], (k, dict((v, k) for (k, v) in v[1].items()))) for (k, v) in _edo_type_map.items())

_doc_type_map = {
    '01': {
        '01': 'декларация',
        '02': 'описание',
        '03': 'доверенность',
        '04': 'подтверждениеДатыОтправки',
        '05': 'уведомлениеОбОтказе',
        '06': 'квитанцияОПриеме',
        '07': 'уведомлениеОбУточнении',
        '08': 'извещениеОВводе',
        '09': 'извещениеОПолучении',
        '10': 'приложение',
    },
    '02': {
        '01': 'обращение',
        '02': 'описание',
        '03': 'приложение',
        '04': 'доверенность',
        '05': 'подтверждениеДатыОтправки',
        '06': 'извещениеОПолучении',
        '07': 'уведомлениеОбОтказе',
        '08': 'подтверждениеДатыПолучения',
    },
    '03': {
        '01': 'письмо',
        '02': 'описание',
        '03': 'приложение',
        '04': 'подтверждениеДатыОтправки',
        '05': 'извещениеОПолучении',
    },
    '04': {
        '01': 'рассылка',
        '02': 'описание',
        '03': 'приложение',
        '04': 'подтверждениеДатыОтправки',
    },
    '05': {
        '01': 'рассылка',
        '02': 'описание',
        '03': 'приложение',
        '04': 'подтверждениеДатыОтправки',
        '05': 'извещениеОПолучении',
    },
    '06': {
        '01': 'запрос',
        '02': 'описание',
        '03': 'доверенность',
        '04': 'подтверждениеДатыОтправки',
        '05': 'квитанцияОПриеме',
        '06': 'уведомлениеОбОтказе',
        '07': 'ответ',
        '08': 'извещениеОПолучении',
        '09': 'подтверждениеДатыПолучения',
    },
    '07': {
        '01': 'сообщениеОбОшибке',
        '02': 'описаниеОшибочногоПакета',
    },
    '08': {
        '01': 'форма2НДФЛ',
        '02': 'описание',
        '03': 'доверенность',
        '04': 'подтверждениеДатыОтправки',
        '05': 'протоколПриема2НДФЛ',
        '06': 'реестрПринятыхДокументов',
        '07': 'извещениеОПолучении',
    },
    '09': {
        '01': 'заявление',
        '02': 'описание',
        '03': 'доверенность',
        '04': 'подтверждениеДатыОтправки',
        '05': 'уведомлениеОбОтказе',
        '06': 'квитанцияОПриеме',
        '07': 'сообщениеОПроверке',
        '08': 'извещениеОПолучении',
        '09': 'сообщениеОбОтзывеЗаявления',
        '10': 'сообщениеОНесоответствиях',
    },
    '10': {
        '01': 'документ',
        '02': 'описание',
        '03': 'приложение',
        '04': 'подтверждениеДатыОтправки',
        '05': 'уведомлениеОбОтказе',
        '06': 'квитанцияОПриеме',
        '07': 'извещениеОПолучении',
    },
    '11': {
        '01': 'уведомление',
        '02': 'описание',
        '03': 'подтверждениеДатыОтправки',
        '04': 'уведомлениеОбОтказе',
        '05': 'квитанцияОПриеме',
        '06': 'извещениеОПолучении',
    },
    '12': {
        '01': 'представление',
        '02': 'описание',
        '03': 'приложение',
        '04': 'доверенность',
        '05': 'подтверждениеДатыОтправки',
        '06': 'квитанцияОПриеме',
        '07': 'уведомлениеОбОтказе',
        '08': 'извещениеОПолучении',
    },
    '13': {
        '01': 'участник',
        '02': 'описание',
        '03': 'подтверждениеДатыОтправки',
        '04': 'квитанцияОПриеме',
        '05': 'уведомлениеОбОтказе',
        '06': 'извещениеОПолучении',
    },
}

_reverse_doctype_map = dict(
    (k, dict((v, k) for (k, v) in v.items())) for (k, v) in _doc_type_map.items())


class Sender(Schema):
    ''' XML-дескриптор отправителя
    '''
    # Идентификатор абонента или спецоператора
    uid = SimpleField('@идентификаторСубъекта')

    # Тип отправителя, значение по умолчанию устанавливается на основе
    # идентификатора отправителя
    type = SimpleField('@типСубъекта', getter='get_type',
                            setter='set_type')

    def get_type(self):
        if hasattr(self, '__type'):
            return self.__type

        if hasattr(self, 'uid'):
            if len(self.uid) == 3:
                return 'спецоператор'
            elif len(self.uid) == 4:
                return 'налоговыйОрган'
            else:
                return 'абонент'

    def set_type(self, value):
        self.__type = value

    class Meta:
        root = 'отправитель'


class SOS(Sender):
    """Дескриптор спецоператора, отличается от отправителя только тегом. """

    class Meta:
        root = 'спецоператор'


class Receiver(Sender):
    """Дескриптор получателя, отличается от отправителя только тегом. """

    class Meta:
        root = 'получатель'


class Document(Schema):
    """Дескриптор документа.

    """
    # атрибуты документа
    type_code = CharField('@кодТипаДокумента', max_length=2,)
    type = SimpleField('@типДокумента')
    content_type = SimpleField('@типСодержимого')
    compressed = BooleanField('@сжат')
    encrypted = BooleanField('@зашифрован')
    uid = SimpleField('@идентификаторДокумента')
    orig_filename = SimpleField('@исходноеИмяФайла', minOccurs=0)

    # содержимое
    content = ComplexField('содержимое',
                                minOccurs=0,

                                filename=SimpleField('@имяФайла')
                                )
    # подписи, представляются в виде списка элементов типа Signature
    signature = ComplexField('подпись',
                                  minOccurs=0,
                                  maxOccurs='unbounded',

                                  role=SimpleField('@роль'),
                                  filename=SimpleField('@имяФайла'),
                                  )

    def __init__(self, *args, **nargs):
        ''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        super(Document, self).__init__(*args, **nargs)

    class Meta:
        root = 'документ'


class TransInfo(Schema):
    """ XML-дескриптор контейнера.

    """
    version = SimpleField('@версияФормата', default="ФНС:1.0")
    doc_code = CharField('@кодТипаДокументооборота', max_length=2)
    doc_type = SimpleField('@типДокументооборота')
    trans_code = CharField('@кодТипаТранзакции', max_length=2)
    transaction = SimpleField('@типТранзакции')
    uid = SimpleField('@идентификаторДокументооборота')
    soft_version = SimpleField('@ВерсПрог', minOccurs=0)
    sender = ComplexField(Sender)
    sos = ComplexField(SOS, minOccurs=0)
    receiver = ComplexField(Receiver)
    extra = RawField('ДопСв', minOccurs=0)
    # документы представляются в виде списка
    doc = ComplexField(Document, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        root = 'ТрансИнф'


class ContainerFNS(Zipped, ContainerUtil, TransInfo):
    """Docstring for ContainerFNS """

    protocol = 7

    def __init__(self, *args, **nargs):
        ''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        self.file_uid = uuid4().hex
        super(ContainerFNS, self).__init__(*args, **nargs)

    def add_file(self, *args, **nargs):
        doc = super(ContainerFNS, self).add_file(*args, **nargs)
        doc.type_code = _reverse_doctype_map[self.trans_code][doc.type]

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
