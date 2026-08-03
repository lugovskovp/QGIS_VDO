# About
Systeme Guidage Carminat C-IQ navigation database QGIS viewer This plugin for view/explore a digital road map database for the CARiN- and VDODayton navigation compatible systems

Плагин для просмотра в QGIS данных файлов навигационных систем VDO Dayton CD, устанавливавшихся на Citroen, Pegout, BMW, Mercedes, Fiat ect с начала 2000 годов.

> [!IMPORTANT]  
> Плагин в процессе разработки, релизов не было, смысла скачивать - пока что нет.


# Версии ПО
 OS-9000/MIPS  V3.0  Copyright (c) 1997-2000 by Microware Systems Corp.
 1991 - 2005 SiemensVDO Automotive AG
 
- QGIS 3.44.10 ltr
- VDO Dayton CD Carindb v.30
- VDO Dayton CD Carindb v.34

- pip install bitarray


# Функциональность
- Выбор файла. Вывод инфо о файле (файлах). Запоминание настроек.
- Выбор страны, города, дороги, точки интереса
- Отображение категорий POI, вывод списка категорий и POI по ним в интерфейс QGIS


# История реверс-инжиниринга формата carindb
Формат данных закрытый, история получения информации по значению данных в файлах VDO Dayton на Habr:
- [Реверс черного тессеракта. Начало](https://habr.com/ru/post/597625/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.2f5d74b3-63ff776e-440b408c-74722d776562/https/habr.com/ru/post/597625/)
- [01. Сшей красное с красным, желтое с желтым, белое с белым. Наверняка будет хорошо](https://habr.com/ru/post/597851/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.1f39f163-63ff7879-fca36fdd-74722d776562/https/habr.com/ru/post/597851/)
- [02. Я уже даже не вижу код. Я вижу блондинку, брюнетку и рыжую](https://habr.com/ru/post/598673/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.7eefa2d2-63ff78ae-7b1bd31b-74722d776562/https/habr.com/ru/post/598673/)
- [03. С прозрачными воротами и яркою звездой](https://habr.com/ru/post/599661/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.feff4f4f-63ff7b3d-64ac638b-74722d776562/https/habr.com/ru/post/599661/)
- [04. The Gold-Bug](https://habr.com/ru/post/645355/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.65863e91-63ff7baa-91e5cf05-74722d776562/https/habr.com/ru/post/645355/)
- i hope to be continued...


# TODO
- [x] Плагин вообще
- [x] Кнопка на панели - скрывает/показывает рабочее поле плагина, пустое поле с краткой справкой
    * [x] иконка
    * [x] кнопка с иконкой на toolbars
    * [x] use QgsMessageLog
    * [x] рабочее поле с заглушкой
    * [x] log = QgisLog("VDOExplorer")
- [x] i18n - интернационализация - text=self.tr(u'Carin C-IQ VDO DB Viewer'),
- [x] Поведение кнопки (mvp): открыть-закрыть файл, настройки
    * [x] нажатие на кнопку подписано, что загружается последний Carindb
    * [x] гармонизированы меню и попап кнопки
    * [x] mockи на нажатия настроек и загрузки
    * [x] settings.py - qt-настройки
- [x] настройки - открываются, редактируются, сохраняются, интернализированы
    * [x] кнопка настроек в меню и у основной кнопки
    * [x] файл settings.py для обеспечения сохранения/чтения настроек
    * [x] сохранение/восстановление параметров при изменении в qt-настройках
    * [x] окно - виджет настроек
    * [x] i18n настроек
- [x] добавить диалог выбора для открытия файла
    * [x] Открывается диалог с default options
    * [x] открывается в заданной папке, если путь из настроек не существует - открыть первый существующий вверх по дереву, либо же открытие в домашней папке (если вообще всё плохо)
    * [x] последний открытый путь сохраняется в настройках 
- [x] Список последних файлов 
    * [x] при успешном открытии перестроить в настройках список файлов - первым этот самый, следующие, но не более числа из настроек - из предыдущего списка
    * [x] initGui генерит строки qafctions из ранее открытых (список в настройках) файлов
    * [x] выделение цветом невалидных (например перемещенных)
    * [x] refresh при апдейте last files
    * [x] refresh при открытии файла
    * [x] очистка списка последних открытых файлов из панели настроек
    * [x] на кнопку - по умолчанию - первый из валидных
    * [x] если файл по указанному пути не существует или же не является carindb - строка есть, но выделена цветом невалидности
    * [x] настройки (к-во последних, очистить список)
    * [x] alertCarindb
    * [x] удаление из настроек из последних файлов
    * [x] i18n
- [x] QGIS валится - разобраться с причинами
    * [x] логирование
    * [x] лог в рабочую папку?
    * [x] логирование по функциям
    * [x] переписать RegenerateMenu
- [x] минимальный бекенд
    * [x] типы данных
    * [x] типы геоданных
    * [x] базовый тип блока
    * [x] распаковка lzw
    * [x] enums
    * [x] блок х12
    * [x] блок х13
- [ ] работа со строковыми данными
    * [x] блок CH_country / country
    * [ ] поиск по наименованию - функция для отладки/тестов
    * [ ] CH_city / city
    * [ ] CH_road / road
    * [ ] CH_poi / poi
    * [ ] keyboard
- [ ] GEO структуры
    * [x] TOC
    * [x] MAP_AREA
    * [x] GEO_CATEGORIES
    * [x] GEO_SHAPES
    * [x] GEO_LINES
    * [x] VERTEXES
    * [ ] POI
    * [x] TSTR
- [ ] блоки карт - 0x14, 0x15, 0x16, 0x1C, 0x1D, 0x1E
    * [x] vdo.block(offset | bladdr) - создание объекта блока
    * [x] базовый гео-блок MVP
    * [ ] гео-объекты генерируются в базовом гео-блоке
        - [x] ТОС и область карты
        - [ ] все объекты - lines & shapes & poi
        - [x] список категорий
        - [x] полигоны - shapes
        - [x] полилинии - lines
        - [x] vertex
        - [ ] poi 
        - [x] tstr_array_ объекта
    * [x] блоки карт - childs базового гео-блока
        - [x] 0x14, 
        - [x] 0x15, 
        - [x] 0x16, 
        - [x] 0x1C, 
        - [x] 0x1D, 
        - [x] 0x1E
- [x] archives - распаковка
    * [x] type 1 for *0x14, 0x15, 0x16, *0x1C, 0x1D, 0x1E
        - [x] categories
        - [x] shapes
        - [x] lines
        - [x] vertex
        - [x] poi - mock по количеству. Принцип упаковки НЕ ПОНЯТЕН
        - [x] tstr
        - [x] str - в основнной бекенд
            * [x] разобраться, где именно и как запакованы надписи
            * [x] хаффмана дерево
            * [x] преамбула перед основным массивом строковой информации - структура
            * [x] программа разбора-распаковки преамбулы + основного массива.
            * [x] функцией класса bitstream в основную программу
        - [x] странное число после ТОС  (05 12 09 00) (a b c d) - параметры распаковки
            * [x] 05: a - для id line - сколько бит читать, если флаг показывает отсутствие - 1-32, 0-this
            * [x] 12: b - для id shape - сколько бит читать, если флаг показывает отсутствие - 1-32, 0-this
            * [x] 09: c - 9 -столько бит в дельте XY vrtx (8, 9, a)
            * [x] 00: d - ? неизвестное, raise, если не 0
        - [x] разбор хвостов tstr - дозаполнить уже распакованные shp/lin
    * [x] type 2, 3
- [x] Рабочее поле - папка с листами, кнопки настройки, открытия файла
    * [x] при открытии проверяется - действительно ли это carindb, если нет - инфосообщение, fault
    * [x] виджет рабочего поля - открыть/создать при загрузке файла
    * [x] закрытие виджета выгружает vdo carindb? НЕТ
    * [x] при закрытии/перезагрузке плагина - удалять виджет
- [x] tab info
    * [x] компоновка
    * [x] свойства файла vdo
    * [x] area A B coords
    * [x] area A B drawing
    * [x] info from block 13
- [ ] tab address
    * [ ] 
- [ ] tab topo
    * [x] block_0x07  SCALES
    * [x] block_0x08  ALMANSC
    * [x] block_0x09  FOLDER_MAPS
    * [x] получение всего содержимого 08, 09 - с координатами
    * [x] tab scales
    * [x] состояние groupButton scales - хранить в сеттингсах
    * [x] debug push button - clear all vdo groups: + pb_DebugClearVDOevent
    * [x] scroll area - how many folders in almanacs
    * [x] draw scale almanac
    * [x] draw folder maps
    * [x] при переключении (и инициализации?) scale - в соответствующую группу нарисовать альманахи/
    * [x] при инициализации, если нет валидного scale, по-умолчанию - 5 (?) scale
    * [x] ускорить отрисовку карт -maps контуры
    * [x] отображать прогресс по картам -maps
    * [ ] проверка что карты уже загружены?
    * [ ]        tab компоновка и наполение: scales, poi_cats, v34: страны, terr_div
        * [ ] listWidget POI Categories - имя, номер
        * [ ] listWidget Countries
        * [ ] listWidget terrDivisions - пока просто перечень стран


- [ ] tab block
    * [x] tabBlock - функция взятия по клику map в текущем scale (и проверить "пустые")
    * [ ] draw in child layer
    * [ ] 

- [ ] отрисовка геообъектов
    * [ ] функция возвращения геообъекта - набора координат точек
    * [ ] архитектура представления геообъектов - по категориям
    * [ ] класс родитель со свойствами раскраски для полилиний и полигонов
    * [ ] раскраска полилиний
    * [ ] раскраска полигонов


* [x] refactor 
    * [x] COORD: __init__ не только из bytes, но и из целого (hlat) или float (lat)
    * [ ] VDO_FILE

* [x] dockWidget размер задается как мин+растягивание содержимым
* [x] tab содержимое - в scroll area
* [ ] почистить bitstream? av_, v_, ??
* [ ] Settings show RecentFiles qty

* [ ] tests
    * [x] локально организовать
    * [x] fixtures (0x12, 0x13, 0x07, 0x0b, 0x0a, 0x0d), как начало ru30, bmw34, ee30
    * [ ] при коммите - только измененные/коммичующиеся по pytest -m "not slow"
    * [x] vdo.datatypes 98 %
    * [x] vdo.geotypes
    * [x] settings 99 %
    * [x] thread 36 %
    * [ ] 
    * [ ] 

* [x] запрет commit при наличии ошибок flake8
* [x] запрет commit при наличии ошибок pytest
* [ ] github workflow
* [ ] выводить процент покрытия кода прямо в README.md репозитория в виде динамического бейджа (badge)
* [ ] 


где искать qtutils
c:/OSGeo4W/apps/Qt5/bin/designer.exe 




# i18n
[В C++/Qt 5 для интернационализации приложений конвейер следующий:](https://www.linux.org.ru/forum/general/14794408?cid=14796450) 
1. В своём коде вы пишете все строки на английском языке не вылезая за пределы таблицы ASCII-символов.
2. Строки, которые нужно локализовать, вы оборачиваете в специальную функцию tr("string").
3. С помощью утилиты lupdate / pylupdate5 вы собираете все эти строки в своём проекте в .ts-файлы.
4. С помощью программы Qt Linguist вы, или нанятый вами переводчик, переводит .ts-файлы на нужные языки.
5. С помощью утилиты lrelease или просто с помощью той же программы Qt Linguist вы компилируете .ts-файлы в .qm-файлы.
6. Внутри исходного кода своей программы с помощью нескольких объектов класса QTranslator вы применяете к своей программе переводы строк в зависимости от системной локали.

Итак:
- ./i18n/QGIS_VDO.pro - файл проекта
- ```pylupdate5 .\i18n\QGIS_VDO.pro```
- c:\Tools\QtLinguist\bin\linguist.exe 

или ```c:\Work\QGIS_VDO\.venv\Scripts\pylupdate5.exe c:\Work\QGIS_VDO\i18n\QGIS_VDO.pro ```
<TS version="2.1">
<TS version="2.1" language="ru_RU" sourcelanguage="en_US">



# useful
- [Язык разметки Markdown: шпаргалка по синтаксису с примерами](https://skillbox.ru/media/code/yazyk-razmetki-markdown-shpargalka-po-sintaksisu-s-primerami/)
- [PyQt5 - Урок 004. Использование QSettings](https://evileg.com/ru/post/219/)
- [Qt Creator](https://github.com/qt-creator/qt-creator)
- [Qt Designer](https://github.com/PyQt5/QtDesigner/releases)
- [PyQt6 — полное руководство для новичков. Продолжение](https://habr.com/ru/companies/skillfactory/articles/648845/)
- [Изменение цвета выделения для определенного элемента (типа QAction) в QMenuBar](https://stackoverflow.com/questions/72316405/change-highlight-color-for-a-specific-item-qaction-type-on-a-qmenubar)
- [Начинаем работать с цифровыми картами (ГИС)](https://habr.com/ru/companies/bft/articles/773814/)
- [wiki/Web_Mercator_projection](https://en.wikipedia.org/wiki/Web_Mercator_projection)
- [30-й меридиан восточной долготы](https://ru.wikipedia.org/wiki/30-%D0%B9_%D0%BC%D0%B5%D1%80%D0%B8%D0%B4%D0%B8%D0%B0%D0%BD_%D0%B2%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%BE%D0%B9_%D0%B4%D0%BE%D0%BB%D0%B3%D0%BE%D1%82%D1%8B)
- [NDF: an effective mobile GIS physical storage model](https://www.spiedigitallibrary.org/conference-proceedings-of-spie/6754/67541W/NDF-an-effective-mobile-GIS-physical-storage-model/10.1117/12.764932.short)
- Торрент лохматого 2007 года. Единственная найденная "ручная" карта РФ VDO/Siemens GPS Россия Беларусь (СНГ + Европа) [ISO](https://rutracker.org/forum/viewtopic.php?t=894615 "Рутрекер")

- VDO Dayton non C-IQ Europa 2013/2014 (BMW, Renault, Opel, Rover) CD70 / DVD90 [ISO](https://rutracker.org/forum/viewtopic.php?t=4694537)
это диск из комплекта европа состоящего из 10 дисков и называеться он VDO Dayton non C-IQ Europa 2012-2013 (BMW, Renault, Opel, Rover)
Страны покрытия:
скрытый текст
		10 CDs v.2012 - 2013
		CD 1 Benelux
		CD 2 Central-Europa
		CD 3 East-Europa
		CD 4 France
		CD 5 Great Britain & Irlande
		CD 6 Germany
		CD 7 Italia/Greece
		CD 8 Scandinavia
		CD 9 Spain & Portugal
		CD 10 Major Roads of Europe

- Карты для устройств VDO/Siemens Dayton non C-IQ CD 2012/2013 Alpen - Австрия, Швейцария, Германия, Франция, Италия [ISO](https://rutracker.org/forum/viewtopic.php?t=4185746)

- Обновление операционной системы для навигатора VDO Dayton MS5000-Os Update-MO5076 [ISO](https://rutracker.org/forum/viewtopic.php?t=1729907)

# unicode color symbols
КРАСНОЕ ЯБЛОКО (&#x1F34E;): 🍎
ЗЕЛЕНОЕ ЯБЛОКО (&#x1F34F;): 🍏
ГОЛУБОЕ СЕРДЦЕ (&#x1F499;): 💙
ЗЕЛЕНОЕ СЕРДЦЕ (&#x1F49A;): 💚
ЖЕЛТОЕ СЕРДЦЕ (&#x1F49B;): 💛
ФИОЛЕТОВОЕ СЕРДЦЕ (&#x1F49C;): 💜
ЗЕЛЕНАЯ КНИГА (&#x1F4D7;): 📗
СИНЯЯ КНИГА (&#x1F4D8;): 📘
ОРАНЖЕВАЯ КНИГА (&#x1F4D9;): 📙
БОЛЬШОЙ КРАСНЫЙ КРУГ (&#x1F534;): 🔴
БОЛЬШОЙ СИНИЙ КРУГ (&#x1F535;): 🔵
КРУПНЫЙ ОРАНЖЕВЫЙ БРИЛЛИАНТ (&#x1F536;): 🔶
БОЛЬШОЙ ГОЛУБОЙ БРИЛЛИАНТ (&#x1F537;): 🔷
МАЛЕНЬКИЙ ОРАНЖЕВЫЙ БРИЛЛИАНТ (&#x1F538;): 🔸
МАЛЕНЬКИЙ ГОЛУБОЙ БРИЛЛИАНТ (&#x1F539;): 🔹
КРАСНЫЙ ТРЕУГОЛЬНИК, НАПРАВЛЕННЫЙ ВВЕРХ (&#x1F53A;): 🔺
КРАСНЫЙ ТРЕУГОЛЬНИК, НАПРАВЛЕННЫЙ ВНИЗ (&#x1F53B;): 🔻
МАЛЕНЬКИЙ КРАСНЫЙ ТРЕУГОЛЬНИК, НАПРАВЛЕННЫЙ ВЕРШИНОЙ ВВЕРХ (&#x1F53C;): 🔼
МАЛЕНЬКИЙ КРАСНЫЙ ТРЕУГОЛЬНИК ВЕРШИНАМИ ВНИЗ (&#x1F53D;): 🔽