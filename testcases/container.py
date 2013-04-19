#-*- coding:utf-8 -*-

"""Модуль предназначен для работы с контейнерами ФНС."""
import zipfile
import cStringIO
import xml.dom.minidom


class Container(object):
    """Класс для работы с контейнерами"""

    def __init__(self, name, content):
        """

        Метод инициирует объект.

        :param name: имя  контнйнера
        :type name: str
        :param content: содержимое  контейнера
        :type content: str
        :return: None
        :rtype: None
        """

        self.name = name
        self.content = content

        zipcontent = cStringIO.StringIO(content)
        container = zipfile.ZipFile(zipcontent, 'r')
        description = container.read('packageDescription.xml').replace('\n', '')

        self.dom = xml.dom.minidom.parseString(container.read('packageDescription.xml').replace('\n', ''))
        self.sender = self.dom.getElementsByTagName(u'отправитель')[0].getAttribute(u'идентификаторСубъекта')
        self.receiver = self.dom.getElementsByTagName(u'получатель')[0].getAttribute(u'идентификаторСубъекта')
        self.uid = self.dom.documentElement.getAttribute(u'идентификаторДокументооборота')
        self.transaction = self.dom.documentElement.getAttribute(u'типТранзакции')
        self.transaction_code = self.dom.documentElement.getAttribute(u'кодТипаТранзакции')
        self.document = self.dom.getElementsByTagName(u'документ')[0].getAttribute(u'типДокумента')
        self.files = []

        # определяем главный документ для ФНС
        for document_node in self.dom.getElementsByTagName(u'документ'):
            name = document_node.getElementsByTagName(u'исходноеИмяФайла')
            self.files.append(name)


class ContainerFNS(Container):
    pass


class ContainerPFR(Container):
    pass

    def is_positive(self):
        if self.transaction != u'протокол':
            raise Exception('Illegal type transaction')
        for item in self.dom.getElementsByTagName(u'документ'):
            attr = item.getAttribute(u'типДокумента')
            if attr.startswith(u'пачка') or attr.startswith(u'реестрДСВ'):
                return True
        return False


class ContainerSTAT(Container):
    pass


class ContainerEGR(Container):
    def __init__(self, name, content):
        Container.__init__(self, name, content)
        try:
            self.bin = self.dom.getElementsByTagName(u'содержимое')[0].getAttribute(u'имяФайла')
        except IndexError:
            self.bin = None

