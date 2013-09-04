# coding: utf-8
from nose.tools import raises
from xml_orm.core import Schema, DefinitionError, ValidationError, SerializationError, _has_lxml
from xml_orm.util import Zipped
from xml_orm.fields import *
from xml_orm.inspect import inspect_xsd
from zipfile import ZipFile
import sys
from tempfile import mkstemp
from datetime import datetime, time
from glob import iglob

if sys.version_info >= (3,):
    basestring = str
    unicode = str
    bytes = bytes
else:
    basestring = basestring
    unicode = unicode
    bytes = str


class Document(Schema):
    uid = IntegerField(u'ИД')
    abzats = SimpleField.T(minOccurs=0)
    name = CharField(u'ИмяФайла', max_length=255)
    optional = FloatField.A(minOccurs=0)

    class Meta:
        root = u'Документ'
        namespace = 'http://www.example.com/ns2'
        encoding = 'cp1251'


class Author(Schema):
    name = SimpleField(u'Имя')
    surname = SimpleField(u'Фамилия')
    is_poet = BooleanField(u'Поэт')

    class Meta:
        root = u'Автор'


class Signature(Schema):
    uid = CharField(u'@ИД', max_length=32, qualify=True)
    probability = FloatField(u'Вероятность')
    surname = SimpleField.T()

    class Meta:
        root = u'Подпись'
        namespace = 'http://www.example.com/signature'


class Book(Schema):
    uid = CharField(u'@ИД', max_length=32)
    auth = ComplexField(Author)
    doc = ComplexField(Document, minOccurs=0, maxOccurs='unbounded')
    signer = ComplexField(Signature, minOccurs=0)
    price = DecimalField(u'Цена', decimal_places=2, max_digits=10)

    class Meta:
        root = u'Книга'
        namespace = 'http://www.example.com/ns1'


class Article(Book):
    uid = SimpleField(u'ИД', insert_after='auth')
    auth = SimpleField(u'Author')
    izdat = SimpleField(u'Издательство', insert_before='auth',
                        minOccurs=0)

    class Meta:
        root = u'Статья'
        namespace = 'http://www.example.com/ns1'
        encoding = 'utf-8'
        pretty_print = True
        xml_declaration = True


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
    print(b)
    assert unicode(a) == unicode(b) == unicode(c)


def test_nested():
    class Doc(Schema):
        author = CharField('author', max_length=100)
        chapter = ComplexField(
            u'glava',
            title=SimpleField.A(),
            p=SimpleField.A(maxOccurs='unbounded'),
            minOccurs=0,
            maxOccurs='unbounded',)

        class Meta:
            root = 'doc'

    d = Doc(author='Ivan Petrov')
    for i in range(1, 2):
        d.chapter.append(
            d.Chapter(title='Chapter {0}'.format(i),
                      p=['Paragraph {0}.{1}'.format(i, j) for j in range(1, 4)]))
    print(str(d))
    assert str(
        d) == '<doc><author>Ivan Petrov</author><glava title="Chapter 1" p="Paragraph 1.1 Paragraph 1.2 Paragraph 1.3"/></doc>'
    d2 = Doc.load(str(d))
    assert str(d2) == str(d)


def test_split_attr():
    class A(Schema):
        split = IntegerField.A(maxOccurs=10)

    a = A(split=[1, 2, 3, 4, 5])
    assert str(a) == '<A split="1 2 3 4 5"/>'
    b = A.load('<A split="1 2 3 4 5"/>')
    assert len(b.split) == 5 and all(isinstance(x, int) for x in b.split)


@raises(SerializationError)
def test_split_attr_bad():
    class A(Schema):
        split = IntegerField.A(maxOccurs=10)

    a = A(split=list(range(11)))
    str(a)


@raises(ValidationError)
def test_split_attr_bad2():
    class A(Schema):
        split = IntegerField.A(maxOccurs=10)

    A.load('<A split="1 2 3 4 5 6 7 8 9 10 11"/>')


@raises(DefinitionError)
def test_bad_complex_field():
    class A(Schema):
        bad = ComplexField.A()


def test_interleaved_text():
    class InterleavedText(Schema):
        text1 = IntegerField(is_text=1)
        elt1 = CharField('elt', max_length=1)
        text2 = IntegerField(is_text=1)
        elt2 = CharField('elt', max_length=1)

        class Meta:
            root = 'inter'
            pretty_print = True

    it = InterleavedText(text1='1', elt1='a', text2='2', elt2='b')
    print(it)
    it2 = InterleavedText.load('<inter>1<elt>a</elt>2<elt>b</elt></inter>')
    assert (unicode(it).strip() == unicode(it2).strip()
            == '<inter>1<elt>a</elt>2<elt>b</elt></inter>')


@raises(DefinitionError)
def test_bad_inheritance():
    class GoodSchema(Schema):
        s = SimpleField()

    class AnotherGoodSchema(Schema):
        s = SimpleField()

    class BadSchema(GoodSchema, AnotherGoodSchema):
        pass


@raises(DefinitionError)
def test_bad_max_occurs():
    class BadSchema(Schema):
        s = SimpleField(maxOccurs=0)


def test_decimal():
    class GoodDecimal(Schema):
        num = DecimalField(is_text=1, max_digits=3, decimal_places=2)

        class Meta:
            root = 'decimal'

    d = GoodDecimal(num=123.5)
    assert unicode(d) == '<decimal>123.50</decimal>'


@raises(SerializationError)
def test_missing_fields():
    class GoodSchema(Schema):
        req = IntegerField('reqired')

        class Meta:
            root = 'doc'

    badvalue = GoodSchema()
    str(badvalue)


def test_restrict():
    class A(Schema):
        restricted = IntegerField(restrict=[1, 2, 3])

    s = A(restricted=1)
    str(s)


@raises(SerializationError)
def test_restrict_bad():
    class A(Schema):
        restricted = IntegerField(restrict=[1, 2, 3])

    s = A(restricted=4)
    str(s)


@raises(SerializationError)
def test_max_occurs():
    class GoodSchema(Schema):
        limited = IntegerField('reqired', maxOccurs=10)

        class Meta:
            root = 'doc'

    badvalue = GoodSchema(limited=list(range(11)))
    str(badvalue)


@raises(SerializationError)
def test_min_occurs():
    class GoodSchema(Schema):
        limited = IntegerField('reqired', maxOccurs=10, minOccurs=3)

        class Meta:
            root = 'doc'

    badvalue = GoodSchema(limited=list(range(2)))
    str(badvalue)


@raises(ValidationError)
def test_decimal_valid():
    class GoodDecimal(Schema):
        num = DecimalField(max_digits=3, decimal_places=2)

        class Meta:
            root = 'decimal'

    GoodDecimal.load('<decimal>abcdef</decimal>')


def test_empty_list():
    class Cont(Schema):
        optional = ComplexField(
            'opt',
            minOccurs=0,
            maxOccurs='unbounded',

            att=SimpleField('@att', minOccurs=0))

        class Meta:
            root = 'containter'

    c = Cont()
    str(c)


@raises(ValidationError)
def test_missing_element():
    class GoodSchema(Schema):
        num = ComplexField('num', val=IntegerField())

        class Meta:
            root = 'item'

    GoodSchema.load('<item></item>')


@raises(ValidationError)
def test_non_empty():
    class GoodSchema(Schema):
        empty = ComplexField('empty')

        class Meta:
            root = 'item'

    GoodSchema.load('<item><empty>1</empty></item>')


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
    print(a.xml().tag)
    assert 'false' in unicode(a)


def test_new_syntax():
    class newsch(Schema):
        f1 = SimpleField.A(default='f1')
        f2 = ComplexField(
            f1=ComplexField(
                f1=SimpleField.A(default="f2.f1.f1"),
                f2=SimpleField.A(default="f2.f1.f2")),
            f2=SimpleField.A(default="f2.f2"),)

        class Meta:
            pretty_print = 1

    a = newsch(f2=newsch.F2(f1=newsch.F2.F1()))
    print(a)
    b = newsch.load('''
<newsch f1="f1">
  <f2 xmlns="" f2="f2.f2">
    <f1 f1="f2.f1.f1" f2="f2.f1.f2"/>
  </f2>
</newsch>
    ''')
    c = newsch.load(str(a))
    assert unicode(a) == unicode(b) == unicode(c)


def test_repr():
    class A(Schema):
        a = IntegerField.A()
        b = ComplexField(
            c=IntegerField.A(),
            d=IntegerField.A(),
            e=ComplexField(f=CharField(max_length=3, is_attribute=False))
        )

    a = A()
    a.a = 1
    a.b = A.B()
    a.b.c = 1
    a.b.d = 2
    a.b.e = A.B.E(f="3")
    print(repr(a))
    assert repr(a) == "A(a=1, b=A.B(c=1, d=2, e=A.B.E(f='3')))"
    b = eval(repr(a), {}, locals())
    print(repr(b))
    print(str(b))
    assert str(b) == '<A a="1"><b c="1" d="2"><e><f>3</f></e></b></A>'


def test_zipped():
    tmpzip = mkstemp('.zip')[1]

    class A(Zipped, Schema):
        a = IntegerField.A()
        b = ComplexField(
            c=IntegerField.A(),
            d=IntegerField.A(),
            e=ComplexField(f=CharField(max_length=3))
        )

        class Meta:
            entry = 'content.xml'

    with ZipFile(tmpzip, 'w') as zf:
        zf.writestr('content.xml', b'<A a="1"><b c="1" d="2"><e><f>3</f></e></b></A>')
        zf.writestr('file1.bin', b'content 1')
        zf.writestr('file2.bin', b'content 2')

    cont1 = A.load(tmpzip)
    assert sorted(cont1.namelist()) == ['content.xml', 'file1.bin', 'file2.bin']
    cont1.unlink('file1.bin')
    cont1.save()
    cont2 = A.load(open(tmpzip, 'rb'))
    cont2.write('file3.bin', b'content 3')
    assert sorted(cont2.namelist()) == ['content.xml', 'file2.bin', 'file3.bin']
    cont2.save()


def test_datetime():
    class Dates(Schema):
        iso = DateTimeField()
        dot_date = DateTimeField(format=u'%d.%m.%Y')
        only_time = DateTimeField(format=u'%H:%M:%S')

    d = Dates(iso=datetime.now(), dot_date=datetime.now(),
              only_time=datetime.now())
    d1 = Dates.load(str(d))

    assert str(d) == str(d1)


def test_pavel():
    class Operator(Schema):
        uid = SimpleField(u'@ИденСОС', min_length=3, max_length=3, default=u'1AE')
        name = SimpleField(u'@НаимОрг', min_length=3, max_length=1000,
                           default=u'ЗАО Калуга Астрал')

        class Meta:
            root = u'СпецОперат'

    class ConfirmOrganisation(Schema):
        operator = ComplexField(Operator)

        class Meta:
            root = u'ОргПодт'

    operator = Operator()
    print(ConfirmOrganisation(operator))


def test_positional():
    class A(Schema):
        field1 = SimpleField()
        field2 = SimpleField()
        field3 = SimpleField()

    a = A(1, 2, field3=3)
    assert a.field1 == 1 and a.field2 == 2 and a.field3 == 3


@raises(DefinitionError)
def test_positional_extra_args():
    class A(Schema):
        field1 = SimpleField()
        field2 = SimpleField()
        field3 = SimpleField()

    a = A(1, 2, 3, 4, field3=3)
    assert a.field1 == 1 and a.field2 == 2 and a.field3 == 3


def test_pattern():
    class A(Schema):
        field1 = SimpleField(pattern=r'\d{10}')
        field2 = FloatField(pattern=r'0\.\d{3}')
        field3 = IntegerField(pattern=r'2.5')
        field4 = DateTimeField(format=u'%H:%M:%S', pattern=r'12:30:.*')
        field5 = CharField(pattern=r'a.*', max_length=18)

    a = A('1234567891', 0.123, 245)
    a.field4 = time(hour=12, minute=30)
    a.field5 = 'abrashvabra'
    assert str(a)


@raises(ValueError)
def test_pattern_bad():
    class A(Schema):
        field1 = SimpleField(pattern=r'\d{10}')

    unicode(A('asldkjasdlk'))


@raises(ValueError)
def test_pattern_bad3():
    class A(Schema):
        field1 = CharField(pattern=r'a.*', max_length=18)

    unicode(A('bslasdk'))


@raises(ValueError)
def test_pattern_bad2():
    class A(Schema):
        field1 = DateTimeField(format=u'%H:%M:%S', pattern=r'12:30:.*')

    a = A()
    a.field1 = time(hour=19, minute=40)
    unicode(a)


def test_namespace_inherit():
    class Container(Schema):
        class Meta:
            namespace = 'some_ns'

        inherit = ComplexField(
            attr=SimpleField.A()
        )
        not_inherit = ComplexField(
            attr=SimpleField.A(),
            qualify=False
        )

    c = Container(
        inherit=Container.Inherit(attr=100),
        not_inherit=Container.Not_inherit(attr=200),)
    print(c)
    assert str(
        c) == '<Container xmlns="some_ns"><inherit attr="100"/><not_inherit xmlns="" attr="200"/></Container>'


def test_pattern_validation():
    class A(Schema):
        field1 = SimpleField.A(pattern=r'\d{10}')

    a = A.load('<A field1="1234567891"/>')
    assert a.field1 == '1234567891'


@raises(ValidationError)
def test_pattern_validation_bad():
    class A(Schema):
        field1 = SimpleField.A(pattern=r'\d{10}')

    A.load('<A field1="adsasdas"/>')


def test_choice():
    class FromSchema(Schema):
        x = SimpleField()
        y = IntegerField()
        z = FloatField()

    class A(Schema):
        f1 = SimpleField()
        cf1 = ChoiceField(FromSchema, maxOccurs='unbounded')
        cf2 = ChoiceField(a=SimpleField(),
                          b=IntegerField(),
                          c=FloatField(),)

    a = A(1, [A.Cf1(x="test"), A.Cf1(y=3)], A.Cf2(c=3.5))
    print(repr(a))
    sa = unicode(a)
    print(sa)
    b = A.load(sa)
    print(b)
    assert sa == str(b)


def test_override_tag():
    class B(Schema):
        a = IntegerField(default=1)
        b = FloatField(default=2.3)

    class A(Schema):
        c = CharField(max_length=10, default='12345')
        d = ComplexField(B, tag='D')
        e = ComplexField(B)
        f = ComplexField(ref='B', tag='F')

    a = A(d=B(), e=A.E(), f=B())
    print(a)
    assert str(
        a) == '<A><c>12345</c><D><a>1</a><b>2.3</b></D><B><a>1</a><b>2.3</b></B><F><a>1</a><b>2.3</b></F></A>'


def test_recursive():
    class A(Schema):
        forward = ComplexField(ref='B', minOccurs=0, maxOccurs='unbounded')

    class B(Schema):
        backward = ComplexField(ref='A', minOccurs=0, maxOccurs='unbounded')
        sideways = ComplexField(ref='C', minOccurs=0, maxOccurs='unbounded')

    class C(Schema):
        tuda = ComplexField(ref='A', minOccurs=0, maxOccurs='unbounded')
        suda = ComplexField(ref='B', minOccurs=0, maxOccurs='unbounded')

        class Meta:
            root = 'Some'

    c = C(tuda=A(forward=B(backward=A(forward=B()))), suda=B(sideways=C(tuda=A())),)
    print(c)
    assert str(c) == '<Some><A><B><A><B/></A></B></A><B><Some><A/></Some></B></Some>'


def test_reverse():
    class B(Schema):
        u'''
        документация к классу B
        '''
        a = CharField(max_length=10)
        b = IntegerField(default=3)

    class A(Schema):
        u'''
        документация к классу A
        '''
        f = SimpleField()
        c = ComplexField(B)
        d = FloatField('@D', default=0.5)
        e = ChoiceField(ref='B')

    reverse = A.reverse()
    compile(reverse, '<string>', 'exec')


def test_inspect():
    for f in iglob('testcases/*.xsd'):
        print(f)
        res = inspect_xsd(unicode(f))
        assert len(res)
        assert all(compile(r.reverse(), '<string>', 'exec') for r in res)
