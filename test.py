# coding: utf-8
import core


class Document(core.Schema):
    uid = core.SimpleField(u'ИД')
    name = core.SimpleField(u'ИмяФайла')

    class Meta:
        root = u'Документ'
        namespace = u'http://www.example.com/ns2'
        encoding='cp1251'


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
    docs = core.ComplexField(Document, minOccurs=0, maxOccurs='unbounded',
                             use_schema_ns=False)
    signer = core.ComplexField(Signature, minOccurs=0)
    abzats = core.SimpleField(u'Абзац')

    class Meta:
        root = u'Книга'
        namespace = u'http://www.example.com/ns1'


class Article(Book):
    uid = core.SimpleField(u'ИД', insert_after='auth')
    auth = core.SimpleField(u'Author')
    izdat = core.SimpleField(u'Издательство', insert_before='auth',
                             minOccurs=0)

    class Meta:
        root = u'Статья'
        namespace = u'http://www.example.com/ns1'
        encoding = u'cp1251'
        pretty_print = True

    def f(self):
        return str(self)

a = Article(uid=1, auth=u'Иван')
a.abzats = u'Абзац'
a.izdat = u'Мурзилка'
a.docs.append(Document(uid=1, name='xxx'))
a.docs.append(Document(uid=2, name='yyy'))
a.signer = Signature(surname=u'Большой начальник', uid=2)
xml_string = str(a)
print unicode(a)
b = Article.load(xml_string)
assert unicode(a) == unicode(b)
