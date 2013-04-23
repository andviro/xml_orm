#!/usr/bin/env python
#-*- coding: utf-8 -*-

from ..fields import *
from .fns import Document, ContainerFNS
from io import StringIO

u'''
_edo_type_map = {'код документооборота': ('тип документооборота', {
                  'код транзакции': 'тип транзакции',
                  })
                 }

'''
_edo_type_map = {
    '20': (u'СчетФактура', {
           '01': u'СчетФактураПродавец',
           '02': u'ПодтверждениеДатыПоступленияСФ',
           '03': u'ПодтверждениеДатыОтправкиСФ',
           '04': u'ДатаПоступленияСФПродавец',
           '05': u'ДатаОтправкиСФПокупатель',
           '06': u'ИзвещениеПолученияСФПокупатель',
           '07': u'ПодтверждениеДатыОтправкиИзвещения',
           '08': u'ДатаОтправкиИзвещенияПокупатель',
           '09': u'УведомлениеОбУточненииПокупатель',
           '10': u'ИзвещениеПолученияУведомленияПродавец'
           })
}

_reverse_edo_map = dict(
    (v[0], (k, dict((v, k) for (k, v) in v[1].items()))) for (k, v) in _edo_type_map.items())

_doc_type_map = {
    '01': u'счетфактура',
    '02': u'описание',
    '03': u'доверенность',
    '04': u'подтверждениеДатыПоступления',
    '05': u'подтверждениеДатыОтправки',
    '06': u'извещениеОПолучении',
    '07': u'уведомлениеОбУточнении'
}

_reverse_doctype_map = dict((k, dict((v, k) for (k, v) in
                                     _doc_type_map.items())) for k in _edo_type_map)

_edi_schema = StringIO(u'''
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
                        <xs:attribute name="ОжидаетсяПодписьПолучателя" type="xs:boolean"
                            use="optional" default="false">
                            <xs:annotation>
                                <xs:documentation>Признак необходимости подписи получателя </xs:documentation>
                            </xs:annotation>
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
            <xs:attribute name="ВерсПрог" use="required">
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


class EDIDocument(Document):
    sign_required = BooleanField(u'@ОжидаетсяПодписьПолучателя', minOccurs=0)


class ContainerEDI(ContainerFNS):

    protocol = 20

    doc = ComplexField(EDIDocument, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        package = ('EDI_{self.sender.uid}_{self.receiver.uid}_{self.file_uid}'
                   '_{self.doc_code}_{self.trans_code}_{self.doc[0].type_code}.zip')
        schema = _edi_schema
