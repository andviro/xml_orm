#!/usr/bin/env python
#-*- coding: utf-8 -*-

from .. import core
from .fns import Sender, Content, Signature, ContainerFNS, Document, SOS
from uuid import uuid4


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


class PFRSystem(PFRSender):
    u"""Дескриптор получателя, отличается от отправителя только тегом. """

    class Meta:
        root = u'системаОтправителя'


class PFRDocument(core.Schema):
    u"""Дескриптор документа.

    """
    # атрибуты документа
    type = core.SimpleField(u'@типДокумента', default=u'пачкаАДВ')
    content_type = core.SimpleField(u'@типСодержимого', default=u'plain866')
    compressed = core.BooleanField(u'@сжат', default=False)
    encrypted = core.BooleanField(u'@зашифрован', default=False)
    sign_required = core.BooleanField(u'@ОжидаетсяПодписьПолучателя', minOccurs=0)
    uid = core.SimpleField(u'@идентификаторДокумента')

    # содержимое
    content = core.ComplexField(Content)
    # подписи, представляются в виде списка элементов типа Signature
    signature = core.ComplexField(Signature, maxOccurs='unbounded')

    class Meta:
        root = u'документ'


class SKZI(core.Schema):
    u"""Дескриптор документа.

    """
    # атрибуты документа
    type = core.SimpleField(u'@типСКЗИ', default=u'Крипто-Про')

    class Meta:
        root = u'СКЗИ'


class PFRInfo(core.Schema):
    # атрибуты
    version = core.SimpleField(u'@версияФормата', default=u"1.2")
    doc_type = core.SimpleField(u'@типДокументооборота', default=u"СведенияПФР")
    transaction = core.SimpleField(u'@типТранзакции', default=u'сведения')
    uid = core.SimpleField(u'@идентификаторДокументооборота')
    date = core.SimpleField(u'@датаВремяПоступления', minOccurs=0)
    # элементы
    skzi = core.ComplexField(SKZI)
    sender = core.ComplexField(PFRSender)
    sos = core.ComplexField(PFRSystem)
    receiver = core.ComplexField(PFRReceiver)
    extra = core.RawField(u'расширения', minOccurs=0)
    files = core.ComplexField(Document, maxOccurs='unbounded')

    class Meta:
        root = u'пакет'


class ContainerPFR(ContainerFNS):

    class Meta:
        root = u'Пакет'

    protocol = 2

    @property
    def is_positive(self):
        """@todo: Docstring for is_positive
        :returns: @todo

        """
        assert self.transaction == u'протокол', u'wrong transaction type'
        return any(item.type.startswith(u'пачка') or
                   item.type.startswith(u'реестрДСВ') for item in self.files)
