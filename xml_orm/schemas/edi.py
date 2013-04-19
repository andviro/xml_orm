#!/usr/bin/env python
#-*- coding: utf-8 -*-

from .. import core
from .fns import Document, ContainerFNS


class EDIDocument(Document):
    sign_required = core.BooleanField(u'@ОжидаетсяПодписьПолучателя', minOccurs=0)


class ContainerEDI(ContainerFNS):

    protocol = 20

    doc = core.ComplexField(EDIDocument, minOccurs=0, maxOccurs='unbounded')

    class Meta:
        package = ('EDI_{self.sender.uid}_{self.receiver.uid}_{self.file_uid}'
                   '_{self.doc_code}_{self.trans_code}_{self.doc[0].type_code}.zip')
