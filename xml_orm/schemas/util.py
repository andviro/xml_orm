#!/usr/bin/env python
#-*- coding: utf-8 -*-

from uuid import uuid4


class ContainerUtil(object):
    """Примесь для всяких полезных функций, общих для всех контейнеров """

    def __init__(self, *args, **kwargs):
        """@todo: Docstring for __init__
        :returns: @todo

        """
        super(ContainerUtil, self).__init__(*args, **kwargs)
        self.post_init()

    def post_init(self):
        pass

    def add_file(self, filename, doc_type, content_type, content=None,
                 compressed=False, encrypted=False, signature=None, sig_role=None):
        """Добавляет файл в контейнер, а так же в дескриптор контейнера.

        :filename: имя файла
        :content: байтовая строка с содержимым (если отсутствует, данные
            читаются из файла filename)
        :doc_type: название типа документа в данной транзакции/документообороте
        :content_type: название типа документа в данной транзакции/документообороте
        :compressed: флаг наличия сжатия
        :encrypted: флаг наличия шифрования
        :signature: байтовая строка с эл. подписью, может отсутствовать
        :returns: объект типа `Doc()`, добавленный в дескриптор

        """
        doc_uid = uuid4().hex
        doc = self.Doc(uid=doc_uid,
                       type=doc_type,
                       content_type=content_type,
                       compressed=compressed,
                       encrypted=encrypted,
                       orig_filename=filename,
                       content=self.Doc.Content(filename=doc_uid + '.bin'))
        self.write(doc.content.filename, content)
        if signature is not None:
            sig_uid = uuid4().hex
            sig = doc.Signature(filename=sig_uid + '.bin')
            if sig_role is not None:
                sig.role = sig_role
            self.write(sig.filename, signature)
            doc.signature.append(sig)
        self.doc.append(doc)
        return doc
