# Универсальный ORM для XML-контейнеров

Пакет позволяет структурно проектировать схемы XML-документов, аналогично
моделям таблиц БД фреймворка [Django.](https://docs.djangoproject.com/en/dev/topics/db/models/) Объектно-ориентированный подход
позволяет повторно использовать элементы схем путем наследования и
переопределения полей XML-элементов. При задании класса-схемы автоматически
генерируется код для загрузки и сохранения XML-документов, удовлетворяющих
схеме. Также в составе пакета имеется класс-примесь, помещающий XML-контейнер
внутрь архива Zip.

## Установка пакета

Установка производится запуском командной строки:

    python setup.py install

Рекомендуется предварительно создать и активировать виртуальное окружение с
помощью пакета `virtualenv`.

## Документация

Документация поддерживается в [wiki проекта](https://bitbucket.org/andviro/xml_orm/wiki)

