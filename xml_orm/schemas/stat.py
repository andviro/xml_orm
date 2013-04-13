#!/usr/bin/env python
#-*- coding: utf-8 -*-

from .. import core
from .fns import Content, Signature


class StatSender(core.Schema):
    class Meta:
        root = u'отправитель'

    uid = core.SimpleField(u'@идентификаторСубъекта')
    type = core.SimpleField(u'@типСубъекта')
    name = core.SimpleField(u'@названиеОрганизации', minOccurs=0)


class StatSystem(core.Schema):
    class Meta:
        root = u'системаОтправителя'

    uid = core.SimpleField(u'@идентификаторСубъекта')
    type = core.SimpleField(u'@типСубъекта')


class StatReceiver(StatSystem):
    class Meta:
        root = u'получатель'


class StatDocument(core.Schema):
    class Meta:
        root = u'документ'

    #содержимое
    content = core.ComplexField(Content, minOccurs=0)
    #подпись
    signature = core.ComplexField(Signature, minOccurs=0, maxOccurs='unbounded')
    type = core.SimpleField(u'@типДокумента')
    content_type = core.SimpleField(u'@типСодержимого')
    compressed = core.SimpleField(u'@сжат')
    encrypted = core.SimpleField(u'@зашифрован')
    uid = core.SimpleField(u'@идентификаторДокумента')


class StatInfo(core.Schema):
    class Meta:
        root = u'пакет'

    version = core.SimpleField(u'@версияФормата', default=u'Стат:1.0')
    uid = core.SimpleField(u'@идентификаторДокументооборота')
    doc_type = core.SimpleField(u'@типДокументооборота')
    transaction = core.SimpleField(u'@типТранзакции')

    #отправитель
    sender = core.ComplexField(StatSender)
    #системаОтправителя
    sos = core.ComplexField(StatSystem, minOccurs=0)
    #получатель
    receiver = core.ComplexField(StatReceiver)
    #документ
    files = core.ComplexField(StatDocument, minOccurs=0, maxOccurs='unbounded')


class ContainerStat(core.Zipped, StatInfo):
    """Docstring for ContainerStat """

    protocol = 4

    class Meta:
        # имя файла с дескриптором в архиве. При наследовании может быть
        # изменено.
        entry = 'packageDescription.xml'

        # кодировка в которой сохранится XML
        encoding = 'cp1251'

        # управление форматированием сохраняемого XML
        pretty_print = True
