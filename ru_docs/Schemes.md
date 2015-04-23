# Схемы XML

## Проектирование схем

Класс `xml_orm.core.Schema` аналогично классу `django.db.models.Model` задает
объектно-ориентированную модель XML-узла. Схема должна наследовать
непосредственно класс `Schema` или один из его потомков. Множественное
наследование схем на данный момент не разрешено, но число предков схемы, не
относящихся к XML ORM, а так же глубина дерева наследования, не ограничены.
Следующий пример определяет схему XML-узла с двумя простыми суб-элементами `ИД`
и `ИмяФайла`, которые будут транслированы в поля `uid` и `name` соответственно:

    :::python
    from xml_orm.core import Schema
    from xml_orm.fields import *

    class Document(Schema):
        uid = SimpleField(u'ИД')
        name = SimpleField(u'ИмяФайла')

        class Meta:
            root = u'Документ'
            namespace = u'http://www.example.com/ns2'
            
Простые поля задаются с помощью классов `SimpleField`, `BooleanField`, и др.
Для них характерно отсутствие дочерних элементов и атрибутов. С такими полями
связываются атомарные значения или списки атомарных значений. Параметры
`minOccurs` и `maxOccurs` определяют, какой вид поле примет в составе объекта.
Если поле имеет `maxOccurs`=1, то оно транслируется в обычное значение, причем,
если задать `minOccurs`=0, то оно будет необязательным к заполнению. Поле с
`maxOccurs` отличным от 1 (это значение не может быть равным 0), транслируется
в список значений. При `minOccurs`=0 такой список по умолчанию инициализируется
в пустое значение.

Класс `Meta` в составе схемы задает неизменные для всех подобных узлов
параметры. В частности `root` задает имя элемента, а `namespace` --
идентификатор пространства имен.

Простое поле может соответствовать как простому суб-элементу XML-узла, так и
его атрибуту. Его вид в XML-документе определяется наличием или отсутствием
префикса `@` в его имени. В следующем примере идентификатор документа из
субэлемента преобразован в атрибут:
    
    :::python
    class NewDocument(Document):
        uid = SimpleField(u'@ИД')

Схема `NewDocument` получена из исходной наследованием. При наследовании, все
поля схемы предка, имена которых совпадают с именами полей потомка,
перекрываются. Новые поля добавляются в конец последовательности полей предка.
Изменить позицию полей потомка в последовательности полей предка можно с
помощью параметров `insert_before` и `insert_after`. В следующем примере поле
`uid` перемещается в конец документа, а новое поле `author` добавляется в его
начало.

    :::python
    class AnotherDocument(Document):
        uid = SimpleField(u'ИД', insert_after='name')
        author = SimpleField(u'Автор', insert_before='name')
        
Мета-информация при наследовании копируется и, при совпадении имен, заменяется:
    
    :::python
    class Article(Document):
        class Meta:
            root = u'Статья'
            encoding = 'windows-1251'
            
## Экземпляры класса `Schema`

### Создание новых экземпляров

Новые экземпляры схемы создаются, как обычные объекты Python, вызовом
конструктора. Конструктору можно передавать именованные параметры, которые
будут записаны в одноименные поля объекта. Непроинициализированные таким образом
поля можно присвоить позже, как обычные поля объекта. В следующем примере
создается экземпляр класса `Article`.

    :::python
    art = Article(uid=1, author=u'Иван', name=u'Влияние войны на мух')
    
### Преобразование в XML

Экземпляр схемы может быть преобразован в объект класса `etree.Element` с
помощью встроенного метода `xml()`. Преобразование будет выполнено, если все 
поля объекта, обязательные к заполнению, инициализированы, в противном
случае будет поднято исключение. 
    
    :::python
    tree = art.xml()

Экземпляр схемы может быть преобразован в байтовую строку или в строку unicode.
Для преобразования в строку можно использовать стандартные функции `str()` и
`repr()`. К сформированному XML-документу добавляется декларация `<?xml ?>` с
кодировкой, которая берется из мета-параметра `encoding`. Его значение по
умолчанию равно `utf-8`.  При отсутствии нужных полей, преобразование в строку
поднимает исключение `SerializationError`, поэтому желательно заключать
его в блоки `try-except` или `with`.

    :::python
    from core import SerializationError
    try:
        print str(art)
    except SerializatonError as err:
        print err

Также экземпляр может быть преобразован в строку unicode, с помощью стандартной
функции `unicode()`. При этом декларация `<?xml ?>` к строке не добавляется.

## Загрузка из файла

Новый экземпляр класса `Schema` можно создать путем загрузки из строки, файла или
файло-подобного объекта, содержащих данные XML. Для этого служит универсальный
метод класса `load()`, принимающий в качестве параметра строку или произвольный
объект, обладающий методом `read()`. В следующем примере создаются три новых
объекта `Article` из трех разных объектов. Предполагается, что на диске
присутствует файл `data.xml`.

    :::python
    fn = 'data.xml'
    fp = open(fn)
    st = open(fn).read()
    
    art1 = Article.load(fn)
    art2 = Article.load(fp)
    art3 = Article.load(st)
    
Загрузка из файла или строки может поднять исключение `ValidationError`,
если загружаемый XML не соответствует схеме.
    
## Сохранение в файл

Потомки класса `Schema` могут переопределять метод `save()`, который по
умолчанию ничего не делает. Класс реализует протокол менеджера контекстов, что
позволяет использовать оператор `with`. При выходе из контекста автоматически
вызывается метод `save()`.
    
    :::python
    class SavedArticle(Article):
        def save(self):
            fn = geattr(self, 'xmlfile', None)
            if fn:
                open(fn, 'w').write(str(self))

    with SavedArticle() as art:
        art.uid = 1
        art.author = u'Иван'
        art.name = u'Влияние войны на мух'
        art.xmlfile = 'article.xml'
        # при выходе из блока файл 'article.xml' будет сохранен

