# coding: utf-8
from xml_orm import core
from nose.tools import raises


class Document(core.Schema):
    uid = core.IntegerField(u'ИД')
    abzats = core.SimpleField(is_text=1, minOccurs=0)
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
    surname = core.SimpleField(is_text=1)

    class Meta:
        root = u'Подпись'
        namespace = u'http://www.example.com/signature'


class Book(core.Schema):
    uid = core.CharField(u'@ИД', max_length=32)
    auth = core.ComplexField(Author)
    doc = core.ComplexField(Document, minOccurs=0, maxOccurs='unbounded')
    signer = core.ComplexField(Signature, minOccurs=0)
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
        pretty_print = True


def test_all_fields():
    a = Article(uid=1, auth=u'Иван')
    a.izdat = u'Мурзилка'
    a.price = 1.3
    a.doc.append(a.Doc(uid=1, name='xxx', abzats=u'абзац'))
    a.doc.append(a.Doc(uid=2, name='yyy'))
    a.signer = a.Signer(surname=u'Большой начальник', uid=100, probability=0.4)
    test_xml = u'''<Статья xmlns:t="http://www.example.com/ns1" xmlns="http://www.example.com/ns1">
  <Издательство>Мурзилка</Издательство>
  <Author>Иван</Author>
  <ИД>1</ИД>
  <Документ xmlns:t="http://www.example.com/ns2" xmlns="http://www.example.com/ns2"><ИД>1</ИД>абзац<ИмяФайла>xxx</ИмяФайла></Документ>
  <Документ xmlns:t="http://www.example.com/ns2" xmlns="http://www.example.com/ns2">
    <ИД>2</ИД>
    <ИмяФайла>yyy</ИмяФайла>
  </Документ>
  <Подпись xmlns:t="http://www.example.com/signature"
    xmlns="http://www.example.com/signature"
    t:ИД="100">
    <Вероятность>0.4</Вероятность>
    Большой начальник
  </Подпись>
  <Цена>1.30</Цена>
</Статья>
    '''
    b = Article.load(test_xml)
    c = Article.load(str(a))
    assert unicode(a) == unicode(b) == unicode(c)


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
    d2 = Doc.load(str(d))
    assert str(d2) == str(d)


def test_interleaved_text():
    class InterleavedText(core.Schema):
        text1 = core.IntegerField(is_text=1)
        elt1 = core.CharField('elt', max_length=1)
        text2 = core.IntegerField(is_text=1)
        elt2 = core.CharField('elt', max_length=1)

        class Meta:
            root = 'inter'
            pretty_print = True

    it = InterleavedText(text1='1', elt1='a', text2='2', elt2='b')
    assert unicode(it).strip() == u'<inter>1<elt>a</elt>2<elt>b</elt></inter>'


@raises(core.DefinitionError)
def test_bad_inheritance():
    class GoodSchema(core.Schema):
        s = core.SimpleField()

    class AnotherGoodSchema(core.Schema):
        s = core.SimpleField()

    class BadSchema(GoodSchema, AnotherGoodSchema):
        pass


@raises(core.DefinitionError)
def test_bad_max_occurs():
    class BadSchema(core.Schema):
        s = core.SimpleField(maxOccurs=0)


@raises(core.DefinitionError)
def test_bad_max_length():
    class BadSchema(core.Schema):
        s = core.CharField()


@raises(core.DefinitionError)
def test_bad_precision():
    class BadSchema(core.Schema):
        s = core.DecimalField(max_digits=10)


@raises(core.DefinitionError)
def test_bad_max_digits():
    class BadSchema(core.Schema):
        s = core.DecimalField(decimal_places=2)


def test_decimal():
    class GoodDecimal(core.Schema):
        num = core.DecimalField(is_text=1, max_digits=3, decimal_places=2)

        class Meta:
            root = 'decimal'

    d = GoodDecimal(num=123.5)
    assert unicode(d) == u'<decimal>123.50</decimal>'


@raises(core.ValidationError)
def test_missing_fields():
    class GoodSchema(core.Schema):
        req = core.IntegerField('reqired')

        class Meta:
            root = 'doc'

    badvalue = GoodSchema()
    str(badvalue)


@raises(core.SerializationError)
def test_max_occurs():
    class GoodSchema(core.Schema):
        limited = core.IntegerField('reqired', maxOccurs=10)

        class Meta:
            root = 'doc'

    badvalue = GoodSchema(limited=list(range(11)))
    str(badvalue)


@raises(core.SerializationError)
def test_min_occurs():
    class GoodSchema(core.Schema):
        limited = core.IntegerField('reqired', maxOccurs=10, minOccurs=3)

        class Meta:
            root = 'doc'

    badvalue = GoodSchema(limited=list(range(2)))
    str(badvalue)


@raises(core.ValidationError)
def test_decimal_valid():
    class GoodDecimal(core.Schema):
        num = core.DecimalField(max_digits=3, decimal_places=2)

        class Meta:
            root = 'decimal'

    GoodDecimal.load(u'<decimal>abcdef</decimal>')


def test_empty_list():
    class Cont(core.Schema):
        optional = core.ComplexField(
            'opt',
            minOccurs=0,
            maxOccurs='unbounded',

            att=core.SimpleField('@att', minOccurs=0))

        class Meta:
            root = 'containter'

    c = Cont()
    str(c)


@raises(core.ValidationError)
def test_missing_element():
    class GoodSchema(core.Schema):
        num = core.ComplexField('num', val=core.IntegerField())

        class Meta:
            root = 'item'

    GoodSchema.load(u'<item></item>')


@raises(core.ValidationError)
def test_non_empty():
    class GoodSchema(core.Schema):
        empty = core.ComplexField('empty')

        class Meta:
            root = 'item'

    GoodSchema.load(u'<item><empty>1</empty></item>')


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


def test_new_syntax():
    class newsch(core.Schema):
        f1 = core.SimpleField(default='f1')
        f2 = core.ComplexField(
            f1=core.ComplexField(
                f1=core.SimpleField(default="f2.f1.f1"),
                f2=core.SimpleField(default="f2.f1.f2")),
            f2=core.SimpleField(default="f2.f2"),)

        class Meta:
            pretty_print = 1

    a = newsch(f2=newsch.F2(f1=newsch.F2.F1()))
    b = newsch.load('''
<newsch>
  <f1>f1</f1>
  <f2>
    <f1>
      <f1>f2.f1.f1</f1>
      <f2>f2.f1.f2</f2>
    </f1>
    <f2>f2.f2</f2>
  </f2>
</newsch>
    ''')
    c = newsch.load(str(a))
    assert unicode(a) == unicode(b) == unicode(c)
