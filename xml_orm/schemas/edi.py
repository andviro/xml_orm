#!/usr/bin/env python
#-*- coding: utf-8 -*-

from .. import core
from .fns import Document, ContainerFNS

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


class EDIDocument(Document):
    sign_required = core.BooleanField(u'@ОжидаетсяПодписьПолучателя', minOccurs=0)


class ContainerEDI(ContainerFNS):

    protocol = 20

    doc = core.ComplexField(EDIDocument, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        package = ('EDI_{self.sender.uid}_{self.receiver.uid}_{self.file_uid}'
                   '_{self.doc_code}_{self.trans_code}_{self.doc[0].type_code}.zip')
