#!/usr/bin/env python
#-*- coding: utf-8 -*-
from uuid import uuid4
from ..core import Schema
from ..util import Zipped
from ..fields import *
from .util import ContainerUtil
from io import StringIO

u'''
_edo_type_map = {'код документооборота': ('тип документооборота', {
                  'код транзакции': 'тип транзакции',
                  })
                 }

'''
_edo_type_map = {
    '01': (u'Декларация', {
           '01': u"ДекларацияНП",
           '02': u"ИзвещениеДекларацияНО",
           '03': u"ИзвещениеПодтверждениеНО",
           '04': u"РезультатПриемаДекларацияНО",
           '05': u"ИзвещениеРезультатПриемаСОС",
           '06': u"ИзвещениеРезультатПриемаНП",
           '07': u"РезультатОбработкиДекларацияНО",
           '08': u"ИзвещениеРезультатОбработкиСОС",
           '09': u"ИзвещениеРезультатОбработкиНП",
           '10': u'ПодтверждениеДекларацияНО',
           '11': u'ИзвещениеПодтверждениеНП',
           }),
    '02': (u"ОбращениеНП", {
           '01': u"ОбращениеНП",
           '02': u"ИзвещениеОбращениеНО",
           '03': u"ИзвещениеПодтверждениеНО",
           '04': u"РезультатПриемаОбращениеНО",
           '05': u"ИзвещениеРезультатПриемаСОС",
           '06': u"ИзвещениеРезультатПриемаНП",
           '10': u'ПодтверждениеОбращениеНО',
           '11': u'ИзвещениеПодтверждениеНП',
           }),
    '03': (u"ПисьмоНО", {
           '01': u"ПисьмоНО",
           '02': u"ПодтверждениеПисьмоСОС",
           '03': u"ИзвещениеПисьмоНП",
           '04': u"ИзвещениеПодтверждениеНО",
           }),
    '04': (u"Рассылка", {
           '01': u"РассылкаНО",
           '02': u"ПодтверждениеРассылкаСОС",
           '03': u"ИзвещениеПодтверждениеНО",
           }),
    '05': (u"РассылкаГрупповая", {
           '01': u"РассылкаНО",
           '02': u"ПодтверждениеРассылкаСОС",
           '03': u"ИзвещениеРассылкаНП",
           '04': u"ИзвещениеПодтверждениеНО",
           }),
    '06': (u"ИОН", {
           '01': u"ЗапросНП",
           '02': u"ИзвещениеЗапросНО",
           '03': u"ИзвещениеПодтверждениеНО",
           '04': u"РезультатПриемаЗапросНО",
           '05': u"ИзвещениеРезультатПриемаСОС",
           '06': u"ИзвещениеРезультатПриемаНП",
           '07': u"РезультатОбработкиЗапросНО",
           '08': u"ИзвещениеРезультатОбработкиСОС",
           '09': u"ИзвещениеРезультатОбработкиНП",
           '10': u'ПодтверждениеЗапросНО',
           '11': u'ИзвещениеПодтверждениеНП',
           }),
    '07': (u"ОшибкаОбработкиПакета", {
           '01': u"СообщениеОбОшибке",
           }),
    '08': (u"Сведения2НДФЛ", {
           '01': u"Форма2НДФЛНП",
           '02': u"ИзвещениеФорма2НДФЛНО",
           '03': u"ИзвещениеПодтверждениеНО",
           '04': u"РезультатПриемаФорма2НДФЛНО",
           '05': u"ИзвещениеРезультатПриемаСОС",
           '06': u"ИзвещениеРезультатПриемаНП",
           '10': u'ПодтверждениеФорма2НДФЛНО',
           '11': u'ИзвещениеПодтверждениеНП',
           }),
}

_reverse_edo_map = dict(
    (v[0], (k, dict((v, k) for (k, v) in v[1].items()))) for (k, v) in _edo_type_map.items())

_doc_type_map = {
    '01': {
        '01': u'декларация',
        '02': u'описание',
        '03': u'доверенность',
        '04': u'подтверждениеДатыОтправки',
        '05': u'уведомлениеОбОтказе',
        '06': u'квитанцияОПриеме',
        '07': u'уведомлениеОбУточнении',
        '08': u'извещениеОВводе',
        '09': u'извещениеОПолучении',
        '10': u'приложение',
    },
    '02': {
        '01': u'обращение',
        '02': u'описание',
        '03': u'приложение',
        '04': u'доверенность',
        '05': u'подтверждениеДатыОтправки',
        '06': u'извещениеОПолучении',
        '07': u'уведомлениеОбОтказе',
        '08': u'подтверждениеДатыПолучения',
    },
    '03': {
        '01': u'письмо',
        '02': u'описание',
        '03': u'приложение',
        '04': u'подтверждениеДатыОтправки',
        '05': u'извещениеОПолучении',
    },
    '04': {
        '01': u'рассылка',
        '02': u'описание',
        '03': u'приложение',
        '04': u'подтверждениеДатыОтправки',
    },
    '05': {
        '01': u'рассылка',
        '02': u'описание',
        '03': u'приложение',
        '04': u'подтверждениеДатыОтправки',
        '05': u'извещениеОПолучении',
    },
    '06': {
        '01': u'запрос',
        '02': u'описание',
        '03': u'доверенность',
        '04': u'подтверждениеДатыОтправки',
        '05': u'квитанцияОПриеме',
        '06': u'уведомлениеОбОтказе',
        '07': u'ответ',
        '08': u'извещениеОПолучении',
        '09': u'подтверждениеДатыПолучения',
    },
    '07': {
        '01': u'сообщениеОбОшибке',
        '02': u'описаниеОшибочногоПакета',
    },
    '08': {
        '01': u'форма2НДФЛ',
        '02': u'описание',
        '03': u'доверенность',
        '04': u'подтверждениеДатыОтправки',
        '05': u'протоколПриема2НДФЛ',
        '06': u'реестрПринятыхДокументов',
        '07': u'извещениеОПолучении',
    },
    '09': {
        '01': u'заявление',
        '02': u'описание',
        '03': u'доверенность',
        '04': u'подтверждениеДатыОтправки',
        '05': u'уведомлениеОбОтказе',
        '06': u'квитанцияОПриеме',
        '07': u'сообщениеОПроверке',
        '08': u'извещениеОПолучении',
        '09': u'сообщениеОбОтзывеЗаявления',
        '10': u'сообщениеОНесоответствиях',
    },
    '10': {
        '01': u'документ',
        '02': u'описание',
        '03': u'приложение',
        '04': u'подтверждениеДатыОтправки',
        '05': u'уведомлениеОбОтказе',
        '06': u'квитанцияОПриеме',
        '07': u'извещениеОПолучении',
    },
    '11': {
        '01': u'уведомление',
        '02': u'описание',
        '03': u'подтверждениеДатыОтправки',
        '04': u'уведомлениеОбОтказе',
        '05': u'квитанцияОПриеме',
        '06': u'извещениеОПолучении',
    },
    '12': {
        '01': u'представление',
        '02': u'описание',
        '03': u'приложение',
        '04': u'доверенность',
        '05': u'подтверждениеДатыОтправки',
        '06': u'квитанцияОПриеме',
        '07': u'уведомлениеОбОтказе',
        '08': u'извещениеОПолучении',
    },
    '13': {
        '01': u'участник',
        '02': u'описание',
        '03': u'подтверждениеДатыОтправки',
        '04': u'квитанцияОПриеме',
        '05': u'уведомлениеОбОтказе',
        '06': u'извещениеОПолучении',
    },
}

_reverse_doctype_map = dict(
    (k, dict((v, k) for (k, v) in v.items())) for (k, v) in _doc_type_map.items())

_fns_schema = StringIO(u'''
<!-- edited with XMLSpy v2007 sp2 (http://www.altova.com) by ЛАПШИН (GNIVC FNS RF) -->
<!-- edited with XMLSPY v2004 rel. 4 U (http://www.xmlspy.com) by Home (Home) -->
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified" attributeFormDefault="unqualified">
    <xs:element name="ТрансИнф">
        <xs:annotation>
            <xs:documentation>Сведения описания транспортной информации</xs:documentation>
        </xs:annotation>
        <xs:complexType>
            <xs:sequence>
                <xs:element name="отправитель">
                    <xs:annotation>
                        <xs:documentation>Отправитель </xs:documentation>
                    </xs:annotation>
                    <xs:complexType>
                        <xs:attribute name="идентификаторСубъекта" use="required">
                            <xs:annotation>
                                <xs:documentation>Идентификатор отправителя</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:minLength value="1"/>
                                    <xs:maxLength value="46"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                        <xs:attribute name="типСубъекта" use="required">
                            <xs:annotation>
                                <xs:documentation>Тип субъекта</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:minLength value="1"/>
                                    <xs:maxLength value="50"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                    </xs:complexType>
                </xs:element>
                <xs:element name="спецоператор" minOccurs="0">
                    <xs:annotation>
                        <xs:documentation>Спецоператор</xs:documentation>
                    </xs:annotation>
                    <xs:complexType>
                        <xs:attribute name="идентификаторСубъекта" use="required">
                            <xs:annotation>
                                <xs:documentation>Идентификатор спецоператора</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:length value="3"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                        <xs:attribute name="типСубъекта" use="required">
                            <xs:annotation>
                                <xs:documentation>Тип субъекта</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:minLength value="1"/>
                                    <xs:maxLength value="50"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                    </xs:complexType>
                </xs:element>
                <xs:element name="получатель">
                    <xs:annotation>
                        <xs:documentation>Получатель</xs:documentation>
                    </xs:annotation>
                    <xs:complexType>
                        <xs:attribute name="идентификаторСубъекта" use="required">
                            <xs:annotation>
                                <xs:documentation>Идентификатор получателя </xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:minLength value="1"/>
                                    <xs:maxLength value="46"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                        <xs:attribute name="типСубъекта" use="required">
                            <xs:annotation>
                                <xs:documentation>Тип субъекта</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:minLength value="1"/>
                                    <xs:maxLength value="50"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                    </xs:complexType>
                </xs:element>
                <xs:element name="ДопСв" minOccurs="0">
                    <xs:annotation>
                        <xs:documentation>Дополнительные сведения</xs:documentation>
                    </xs:annotation>
                    <xs:complexType>
                        <xs:sequence>
                            <xs:any processContents="skip" minOccurs="0" maxOccurs="unbounded"/>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
                <xs:element name="документ" maxOccurs="unbounded">
                    <xs:annotation>
                        <xs:documentation>Сведения о передаваемом документе</xs:documentation>
                    </xs:annotation>
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="содержимое" minOccurs="0">
                                <xs:annotation>
                                    <xs:documentation>Содержимое документа</xs:documentation>
                                </xs:annotation>
                                <xs:complexType>
                                    <xs:attribute name="имяФайла" use="required">
                                        <xs:annotation>
                                            <xs:documentation>Имя файла в контейнере</xs:documentation>
                                        </xs:annotation>
                                        <xs:simpleType>
                                            <xs:restriction base="xs:string">
                                                <xs:minLength value="1"/>
                                                <xs:maxLength value="150"/>
                                            </xs:restriction>
                                        </xs:simpleType>
                                    </xs:attribute>
                                </xs:complexType>
                            </xs:element>
                            <xs:element name="подпись" minOccurs="0" maxOccurs="unbounded">
                                <xs:annotation>
                                    <xs:documentation>Сведения ЭЦП</xs:documentation>
                                </xs:annotation>
                                <xs:complexType>
                                    <xs:attribute name="имяФайла" use="required">
                                        <xs:annotation>
                                            <xs:documentation>Имя файла ЭЦП в контейнере для данного документа</xs:documentation>
                                        </xs:annotation>
                                        <xs:simpleType>
                                            <xs:restriction base="xs:string">
                                                <xs:minLength value="1"/>
                                                <xs:maxLength value="150"/>
                                            </xs:restriction>
                                        </xs:simpleType>
                                    </xs:attribute>
                                    <xs:attribute name="роль" use="required">
                                        <xs:annotation>
                                            <xs:documentation>Роль подписанта </xs:documentation>
                                        </xs:annotation>
                                        <xs:simpleType>
                                            <xs:restriction base="xs:string">
                                                <xs:minLength value="1"/>
                                                <xs:maxLength value="50"/>
                                            </xs:restriction>
                                        </xs:simpleType>
                                    </xs:attribute>
                                </xs:complexType>
                            </xs:element>
                        </xs:sequence>
                        <xs:attribute name="кодТипаДокумента" use="required">
                            <xs:annotation>
                                <xs:documentation>Код типа документа</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:length value="2"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                        <xs:attribute name="типДокумента" use="required">
                            <xs:annotation>
                                <xs:documentation>Тип документа</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:minLength value="1"/>
                                    <xs:maxLength value="50"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                        <xs:attribute name="типСодержимого" use="required">
                            <xs:annotation>
                                <xs:documentation>Тип содержимого документа</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:minLength value="1"/>
                                    <xs:maxLength value="50"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                        <xs:attribute name="сжат" type="xs:boolean" use="required">
                            <xs:annotation>
                                <xs:documentation>Признак сжатия документа</xs:documentation>
                            </xs:annotation>
                        </xs:attribute>
                        <xs:attribute name="зашифрован" type="xs:boolean" use="required">
                            <xs:annotation>
                                <xs:documentation>Признак шифрования</xs:documentation>
                            </xs:annotation>
                        </xs:attribute>
                        <xs:attribute name="идентификаторДокумента" use="required">
                            <xs:annotation>
                                <xs:documentation>Идентификатор документа</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:length value="32"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                        <xs:attribute name="исходноеИмяФайла" use="optional">
                            <xs:annotation>
                                <xs:documentation>Исходное имя файла документа</xs:documentation>
                            </xs:annotation>
                            <xs:simpleType>
                                <xs:restriction base="xs:string">
                                    <xs:minLength value="1"/>
                                    <xs:maxLength value="150"/>
                                </xs:restriction>
                            </xs:simpleType>
                        </xs:attribute>
                    </xs:complexType>
                </xs:element>
            </xs:sequence>
            <xs:attribute name="версияФормата" use="required">
                <xs:annotation>
                    <xs:documentation>Версия формата</xs:documentation>
                </xs:annotation>
                <xs:simpleType>
                    <xs:restriction base="xs:string">
                        <xs:minLength value="1"/>
                        <xs:maxLength value="10"/>
                        <xs:enumeration value="ФНС:1.0"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:attribute>
            <xs:attribute name="кодТипаДокументооборота" use="required">
                <xs:annotation>
                    <xs:documentation>Код типа документооборота</xs:documentation>
                </xs:annotation>
                <xs:simpleType>
                    <xs:restriction base="xs:string">
                        <xs:length value="2"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:attribute>
            <xs:attribute name="типДокументооборота" use="required">
                <xs:annotation>
                    <xs:documentation>Тип документооборота</xs:documentation>
                </xs:annotation>
                <xs:simpleType>
                    <xs:restriction base="xs:string">
                        <xs:minLength value="1"/>
                        <xs:maxLength value="50"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:attribute>
            <xs:attribute name="кодТипаТранзакции" use="required">
                <xs:annotation>
                    <xs:documentation>Код типа транзакции</xs:documentation>
                </xs:annotation>
                <xs:simpleType>
                    <xs:restriction base="xs:string">
                        <xs:length value="2"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:attribute>
            <xs:attribute name="типТранзакции" use="required">
                <xs:annotation>
                    <xs:documentation>Тип транзакции</xs:documentation>
                </xs:annotation>
                <xs:simpleType>
                    <xs:restriction base="xs:string">
                        <xs:minLength value="1"/>
                        <xs:maxLength value="50"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:attribute>
            <xs:attribute name="идентификаторДокументооборота" use="required">
                <xs:annotation>
                    <xs:documentation>Идентификатор докуменооборота</xs:documentation>
                </xs:annotation>
                <xs:simpleType>
                    <xs:restriction base="xs:string">
                        <xs:length value="32"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:attribute>
            <xs:attribute name="ВерсПрог" use="optional">
                <xs:annotation>
                    <xs:documentation>Версия передающей программы</xs:documentation>
                </xs:annotation>
                <xs:simpleType>
                    <xs:restriction base="xs:string">
                        <xs:maxLength value="40"/>
                        <xs:minLength value="1"/>
                    </xs:restriction>
                </xs:simpleType>
            </xs:attribute>
        </xs:complexType>
    </xs:element>
</xs:schema>
''')


class Sender(Schema):
    u''' XML-дескриптор отправителя
    '''
    # Идентификатор абонента или спецоператора
    uid = CharField(u'@идентификаторСубъекта', min_length=1, max_length=46)

    # Тип отправителя, значение по умолчанию устанавливается на основе
    # идентификатора отправителя
    type = SimpleField(u'@типСубъекта', getter='get_type',
                       setter='set_type')

    def get_type(self):
        if hasattr(self, '__type'):
            return self.__type

        if hasattr(self, 'uid'):
            if len(self.uid) == 3:
                return u'спецоператор'
            elif len(self.uid) == 4:
                return u'налоговыйОрган'
            else:
                return u'абонент'

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


class Document(Schema):
    u"""Дескриптор документа.

    """
    # атрибуты документа
    type_code = CharField(u'@кодТипаДокумента', max_length=2,)
    type = SimpleField(u'@типДокумента')
    content_type = SimpleField(u'@типСодержимого')
    compressed = BooleanField(u'@сжат')
    encrypted = BooleanField(u'@зашифрован')
    uid = SimpleField(u'@идентификаторДокумента')
    orig_filename = SimpleField(u'@исходноеИмяФайла', minOccurs=0)

    # содержимое
    content = ComplexField(u'содержимое',
                           minOccurs=0,

                           filename=SimpleField(u'@имяФайла')
                           )
    # подписи, представляются в виде списка элементов типа Signature
    signature = ComplexField(u'подпись',
                             minOccurs=0,
                             maxOccurs=u'unbounded',

                             role=SimpleField(u'@роль'),
                             filename=SimpleField(u'@имяФайла'),
                             )

    def __init__(self, *args, **nargs):
        u''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        super(Document, self).__init__(*args, **nargs)

    class Meta:
        root = u'документ'


class TransInfo(Schema):
    u""" XML-дескриптор контейнера.

    """
    version = SimpleField(u'@версияФормата', default=u"ФНС:1.0")
    doc_code = CharField(u'@кодТипаДокументооборота', max_length=2)
    doc_type = SimpleField(u'@типДокументооборота')
    trans_code = CharField(u'@кодТипаТранзакции', max_length=2)
    transaction = SimpleField(u'@типТранзакции')
    uid = SimpleField(u'@идентификаторДокументооборота')
    soft_version = SimpleField(u'@ВерсПрог', minOccurs=0)
    sender = ComplexField(Sender)
    sos = ComplexField(SOS, minOccurs=0)
    receiver = ComplexField(Receiver)
    extra = RawField(u'ДопСв', minOccurs=0)
    # документы представляются в виде списка
    doc = ComplexField(Document, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        root = u'ТрансИнф'
        schema = _fns_schema


class ContainerFNS(Zipped, ContainerUtil, TransInfo):
    u"""Docstring for ContainerFNS """

    protocol = 7

    def __init__(self, *args, **nargs):
        u''' Инициализация полей, которые не загружаются/сохраняются из
        контейнера. В частности поле file_uid используется только для вновь
        созданных контейнеров при формировании имени архива.
        '''
        self.file_uid = uuid4().hex
        super(ContainerFNS, self).__init__(*args, **nargs)

    def post_init(self):
        # при создании нового экземпляра контейнера ФНС можно не указать либо
        # `doc_code` либо `doc_type`. Незаполненное поле будет присвоено
        # автоматически в соответствии с типом документооборота.

        if not hasattr(self, 'doc_code') and hasattr(self, 'doc_type'):
            self.doc_code = _reverse_edo_map[self.doc_type][0]
        elif hasattr(self, 'doc_code') and not hasattr(self, 'doc_type'):
            self.doc_type = _edo_type_map[self.doc_code][0]

    def add_file(self, *args, **nargs):
        doc = super(ContainerFNS, self).add_file(*args, **nargs)
        if doc.type.isdigit():
            doc.type_code = doc.type
            doc.type = _doc_type_map[self.trans_code][doc.type_code]
        else:
            doc.type_code = _reverse_doctype_map[self.trans_code][doc.type]
        return doc

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
