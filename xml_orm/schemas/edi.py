#!/usr/bin/env python
#-*- coding: utf-8 -*-

from ..fields import *
from .fns import Document, ContainerFNS

'''
_edo_type_map = {'код документооборота': ('тип документооборота', {
                  'код транзакции': 'тип транзакции',
                  })
                 }

'''
_edo_type_map = {
    '20': ('СчетФактура', {
           '01': 'СчетФактураПродавец',
           '02': 'ПодтверждениеДатыПоступленияСФ',
           '03': 'ПодтверждениеДатыОтправкиСФ',
           '04': 'ДатаПоступленияСФПродавец',
           '05': 'ДатаОтправкиСФПокупатель',
           '06': 'ИзвещениеПолученияСФПокупатель',
           '07': 'ПодтверждениеДатыОтправкиИзвещения',
           '08': 'ДатаОтправкиИзвещенияПокупатель',
           '09': 'УведомлениеОбУточненииПокупатель',
           '10': 'ИзвещениеПолученияУведомленияПродавец'
           })
}

_reverse_edo_map = dict(
    (v[0], (k, dict((v, k) for (k, v) in v[1].items()))) for (k, v) in _edo_type_map.items())

_doc_type_map = {
    '01': 'счетфактура',
    '02': 'описание',
    '03': 'доверенность',
    '04': 'подтверждениеДатыПоступления',
    '05': 'подтверждениеДатыОтправки',
    '06': 'извещениеОПолучении',
    '07': 'уведомлениеОбУточнении'
}

_reverse_doctype_map = dict((k, dict((v, k) for (k, v) in
                                     _doc_type_map.items())) for k in _edo_type_map)


class EDIDocument(Document):
    sign_required = BooleanField('@ОжидаетсяПодписьПолучателя', minOccurs=0)


class ContainerEDI(ContainerFNS):

    protocol = 20

    doc = ComplexField(EDIDocument, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        package = ('EDI_{self.sender.uid}_{self.receiver.uid}_{self.file_uid}'
                   '_{self.doc_code}_{self.trans_code}_{self.doc[0].type_code}.zip')
