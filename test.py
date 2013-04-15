# coding: utf-8
from xml_orm import core
from nose.tools import raises


class Document(core.Schema):
    uid = core.IntegerField(u'ИД')
    abzats = core.SimpleField(minOccurs=0)
    name = core.CharField(u'ИмяФайла', max_length=255)

    class Meta:
        root = u'Документ'
        namespace = u'http://www.example.com/ns2'
        encoding = 'cp1251'


class Author(core.Schema):
    name = core.SimpleField(u'Имя')
    surname = core.SimpleField(u'Фамилия')
    is_poet = core.BooleanField(u'Поэт')

    class Meta:
        root = u'Автор'


class Signature(core.Schema):
    uid = core.CharField(u'@ИД', max_length=32, qualify=True)
    probability = core.FloatField(u'Вероятность')
    surname = core.SimpleField()

    class Meta:
        root = u'Подпись'
        namespace = u'http://www.example.com/signature'


class Book(core.Schema):
    uid = core.CharField(u'@ИД', max_length=32)
    auth = core.ComplexField(Author)
    doc = core.ComplexField(Document, minOccurs=0, maxOccurs='unbounded',
                            use_schema_ns=False)
    signer = core.ComplexField(Signature, minOccurs=0, use_schema_ns=True)
    price = core.DecimalField(u'Цена', decimal_places=2, max_digits=10)

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
        encoding = u'utf-8'
        pretty_print = False


def test_all_fields():
    a = Article(uid=1, auth=u'Иван')
    a.izdat = u'Мурзилка'
    a.price = 1.3
    a.doc.append(a.Doc(uid=1, name='xxx', abzats=u'абзац'))
    a.doc.append(a.Doc(uid=2, name='yyy'))
    a.signer = a.Signer(surname=u'Большой начальник', uid=100, probability=0.4)
    b = Article.load(str(a))
    assert unicode(a) == unicode(b)


def test_nested():
    class Doc(core.Schema):
        author = core.CharField('author', max_length=100)
        chapter = core.ComplexField(
            'chapter',
            title=core.SimpleField('title'),
            p=core.SimpleField('p', maxOccurs='unbounded'),
            minOccurs=0,
            maxOccurs='unbounded',)

        class Meta:
            root = 'doc'
            pretty_print = True

    d = Doc(author='Ivan Petrov')
    for i in range(1, 4):
        d.chapter.append(
            d.Chapter(title='Chapter {0}'.format(i),
                      p=['Paragraph {0}.{1}'.format(i, j) for j in range(1, 4)]))
    #print d
    #assert False


@raises(ValueError)
def test_max_length():
    d = Document(uid=1, abzats='text', name='a' * 256)
    str(d)


@raises(ValueError)
def test_float():
    d = Signature(surname=u'Большой начальник', uid=100, probability="asldkasjd")
    str(d)


@raises(ValueError)
def test_int():
    d = Document(uid="not int", abzats='text', name='a' * 255)
    str(d)


def test_bool():
    a = Author(name='monty',
               surname='python',
               is_poet=False)
    assert u'false' in unicode(a)
