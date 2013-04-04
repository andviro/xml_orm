# coding: utf-8
import core


class Document(core.Schema):
    uid = core.SimpleField(u'ИД')
    name = core.SimpleField(u'ИмяФайла')

    class Meta:
        root = u'Документ'
        namespace = u'http://www.example.com/ns2'


class Author(core.Schema):
    name = core.SimpleField(u'Имя')
    surname = core.SimpleField(u'Фамилия')

    class Meta:
        root = u'Автор'


class Signature(core.Schema):
    uid = core.SimpleField(u'@ИД')
    surname = core.SimpleField()

    class Meta:
        root = u'Подпись'


class Book(core.Schema):
    uid = core.SimpleField(u'@ИД')
    auth = core.ComplexField(Author)
    docs = core.ComplexField(Document, minOccurs=0, maxOccurs='unbounded')
    signer = core.ComplexField(Signature, minOccurs=0)
    abzats = core.SimpleField(u'Абзац')

    class Meta:
        root = u'Книга'
        namespace = u'http://www.example.com/ns1'


class Article(Book):
    uid = core.SimpleField(u'ИД', insert_after='auth')
    auth = core.SimpleField(u'Author')

    class Meta:
        root = u'Статья'
        namespace = u'http://www.example.com/ns1'
        encoding = u'cp1251'
        pretty_print = True

    def f(self):
        return str(self)

a = Article(uid=1, auth=u'Иван')
a.abzats = u'Абзац'
a.docs.append(Document(uid=1, name='xxx'))
a.docs.append(Document(uid=2, name='yyy'))
a.signer = Signature(surname=u'Большой начальник', uid=2)
xml_string = str(a)
b = Article.load(xml_string)
assert unicode(a) == unicode(b)
