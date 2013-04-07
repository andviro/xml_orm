# Универсальный ORM для XML-контейнеров

Пакет позволяет структурно проектировать схемы XML-документов, аналогично
моделям таблиц БД фреймворка `Django`. Объектно-ориентированный подход
позволяет повторно использовать элементы схем путем наследования и
переопределения полей XML-элементов. При задании класса-схемы автоматически
генерируется код для загрузки и сохранения XML-документов, удовлетворяющих
схеме. Также в составе пакета имеется класс-примесь, помещающий XML-контейнер
внутрь архива Zip.

## Схемы

Класс `core.Schema` аналогично классу `django.db.models.Model` задает
объектно-ориентированную модель XML-узла. Схема должна наследовать
непосредственно класс `core.Schema` или один из его потомков. Множественное
наследование схем на данный момент не разрешено, но число предков схемы, не
относящихся к XML ORM, а так же глубина дерева наследования, не ограничены.
Следующий пример определяет схему XML-узла с двумя простыми суб-элементами `ИД`
и `ИмяФайла`, которые будут транслированы в поля `uid` и `name` соответственно:

    :::python
    class Document(core.Schema):
        uid = core.SimpleField(u'ИД')
        name = core.SimpleField(u'ИмяФайла')

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
        uid = core.SimpleField(u'@ИД')

Схема `NewDocument` получена из исходной наследованием. При наследовании, все
поля схемы предка, имена которых совпадают с именами полей потомка,
перекрываются. Новые поля добавляются в конец последовательности полей предка.
Изменить позицию полей потомка в последовательности полей предка можно с
помощью параметров `insert_before` и `insert_after`. В следующем примере поле
`uid` перемещается в конец документа, а новое поле `author` добавляется в его
начало.

    :::python
    class AnotherDocument(Document):
        uid = core.SimpleField(u'ИД', insert_after='name')
        author = core.SimpleField(u'Автор', insert_before='name')
        
Мета-информация при наследовании копируется и, при совпадении имен, заменяется:
    
    :::python
    class Article(Document):
        class Meta:
            root = u'Статья'
            encoding = 'windows-1251'
            
## Экземпляры класса `core.Schema`

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
поднимает исключение, поэтому желательно заключать его в блоки `try-except` или
`with`.

    :::python
    try:
        print str(art)
    except:
        print sys.exc_info()[:2]

Также экземпляр может быть преобразован в строку unicode, с помощью стандартной
функции `unicode()`. При этом декларация `<?xml ?>` к строке не добавляется.

## Загрузка из файла

Новый экземпляр класса `core.Schema` можно создать путем загрузки из строки, файла или
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
    
## Сохранение в файл

Потомки класса `core.Schema` могут переопределять метод `save()`, который по
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

## Поля XML

На данный момент поля задаются с помощью классов `core.SimpleField`,
`core.BooleanField` и `core.ComplexField`. Простые поля, не имеющие дочерних
атрибутов и полей задаются классами `SimpleField` и `BooleanField`. Для простых
полей необязательный параметр `tag` задает название соответствующего элемента
или (с префиксом `@`) -- атрибута. Если параметр `tag` не указан, поле
считывается и записывается из текстового содержимого узла. Корректно
отрабатываются несколько текстовых полей, при условии что два текстовых поля не
идут друг за другом, т.к. в этом случае нет способа отделить их друг от друга.

Класс `core.ComplexField` позволяет вводить в состав схемы элементы со сложным
содержимым, т.е., имеющие суб-элементы и атрибуты. Первый обязательный параметр
`cls` задает этому полю схему, которая должна быть классом, совместимым с
`core.Schema`. В следующем примере одна из схем включается в состав другой в
качестве сложного элемента. Название элемента берется из мета-параметра `root`.

    :::python
    class File(core.Schema):
        id = core.SimpleField(u'@id')
        name = core.SimpleField(default=u'Текст элемента')
        
        class Meta:
            root = u'file'
            
    class Directory(core.Schema):
        files = core.ComplexField(File, minOccurs=0, maxOccurs='unbounded')
        
        class Meta:
            root = u'directory'
            
Общими для всех типов полей являются следующие именованные параметры:

* `default` Значение поля по умолчанию. Подлежит валидации в момент инициализации
поля.
* `minOccurs` Минимальное число повторений поля. Необязательные поля имеют это
параметр равным нулю, по умолчанию это значение равно единице.
* `maxOccurs` Максимальное число повторений поля. Может принимать целые
значения от единицы и выше, или особое значение 'unbounded', означающее
неограниченное число повторений.
* `getter` Имя функции в составе класса, которая будет вызываться при доступе к
полю на чтение.
* `setter` Имя функции для записи в поле.
* `insert_after` Служит для управления порядком следования полей в схеме.
Задает имя поля, после которого следует вставить данное поле.
* `insert_before` Задает имя поля, перед которым следует вставить данное поле.

## Класс-примесь `core.Zipped`

В модуле `core` определен класс `Zipped`, который переопределяет стандартные
методы `load()` и `save()` так, что XML-объект загружается из архива в формате
Zip. Другие методы класса `core.Schema` работают без изменений. Для задания
имени файла в архиве, из которого производится загрузка, добавлен мета-параметр
`entry`.

    :::python
    class ZArticle(core.Zipped, Article):
        class Meta:
            entry = 'content.xml'
            
При загрузке новых объектов, метод `load()` может получать имя файла архива,
файло-подобный объект или байтовую строку с загруженным архивом. Если загрузка
была произведена из файла и его имя известно, то имя сохраняется в поле
`package`. Если в поле `package` было автоматически или иным образом записано
имя файла архива, сохранение методом `save()` будет произведено в файл с этим
именем.


    :::python
    with ZArticle.load("archive.zip") as art:
        art.uid = 2
        # данные будут сохранены в файл "archive.zip"
        
    with ZArticle.load(open("some.zip").read()) as art:
        # данные загружены из байтовой строки,
        # поэтому поле package не содержит имени файла
        art.package = "output.zip"
        
        # при выходе из контекста сохранение будет произведено
        # в архив "output.zip"
    
Если на момент вызова `save()` поле `package` так и не было присвоено, имя для
сохранения будет сформировано с помощью мета-параметра `package`. Параметр содержит
шаблон имени файла, при подстановке в который можно использовать сохраняемый
объект и его поля. В следующем примере сохраняемые архивы будут иметь имена
'article1.zip', 'article2.zip' и т.д., в соответствии с атрибутом `uid`.
    
    :::python
    class AutoZArticle(ZArticle):
        class Meta:
            entry = 'content.xml'
            package = 'article{self.uid}.zip'
            
    for i in range(10):
        art = Article(uid=i + 1,
                      author=u'Иван',
                      name=u'Влияние войны на мух')
        art.save()
            
## Что еще осталось сделать

* Задокументировать модуль `standard` и допилить его содержимое;
* Доделать поля FloatField, DecimalField, IntegerField, StringField (последний
с ограничениями по длине) и что-нибудь еще, DateTimeField, например.
* ???
