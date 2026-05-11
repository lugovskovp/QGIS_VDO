# About
Systeme Guidage Carminat C-IQ navigation database QGIS viewer This plugin for view/explore a digital road map database for the CARiN- and VDODayton navigation compatible systems

Плагин для просмотра в QGIS данных файлов навигационных систем VDO Dayton CD, устанавливавшихся на Citroen, Pegout, BMW, Mercedes, Fiat ect с начала 2000 годов.

> [!IMPORTANT]  
> Плагин в процессе разработки, релизов не было, смысла скачивать - пока что нет.


# Версии ПО
- QGIS 3.44.10 ltr
- VDO Dayton CD Carindb v.30
- VDO Dayton CD Carindb v.34


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
- [ ] Кнопка на панели - скрывает/показывает рабочее поле плагина, пустое поле с краткой справкой
    * [x] иконка
    * [x] кнопка с иконкой на toolbars
    * [x] use QgsMessageLog
    * [ ] рабочее поле с заглушкой
    * [x] log = QgisLog("VDOExplorer")
- [x] i18n - интернационализация - text=self.tr(u'Carin C-IQ VDO DB Viewer'),
- [ ] Поведение кнопки: открыть-закрыть файл, путь-по последнему из последних, список последних, настройки (к-во последних, очистить список)
    * [x] нажатие на кнопку подписано, что загружается последний Carindb
    * [x] гармонизированы меню и попап кнопки
    * [x] mockи на нажатия настроек и загрузки
    * [x] settings.py - qt-настройки
    * [ ]
- [ ] Рабочее поле - папка с листами, кнопки настройки, открытия файла
- [ ] настройки - открываются, редактируются, сохраняются


# i18n
[В C++/Qt 5 для интернационализации приложений конвейер следующий:](https://www.linux.org.ru/forum/general/14794408?cid=14796450) 
1. В своём коде вы пишете все строки на английском языке не вылезая за пределы таблицы ASCII-символов.
2. Строки, которые нужно локализовать, вы оборачиваете в специальную функцию tr("string").
3. С помощью утилиты lupdate / pylupdate5 вы собираете все эти строки в своём проекте в .ts-файлы.
4. С помощью программы Qt Linguist вы, или нанятый вами переводчик, переводит .ts-файлы на нужные языки.
5. С помощью утилиты lrelease или просто с помощью той же программы Qt Linguist вы компилируете .ts-файлы в .qm-файлы.
6. Внутри исходного кода своей программы с помощью нескольких объектов класса QTranslator вы применяете к своей программе переводы строк в зависимости от системной локали.
Итак:
1. ./i18n/QGIS_VDO.pro - файл проекта
2. ```pylupdate5 .\i18n\QGIS_VDO.pro```
3. c:\Tools\QtLinguist\bin\linguist.exe 



# useful
- [Язык разметки Markdown: шпаргалка по синтаксису с примерами](https://skillbox.ru/media/code/yazyk-razmetki-markdown-shpargalka-po-sintaksisu-s-primerami/)
- [PyQt5 - Урок 004. Использование QSettings](https://evileg.com/ru/post/219/)
- [Qt Creator](https://github.com/qt-creator/qt-creator)
- [Qt Designer](https://github.com/PyQt5/QtDesigner/releases)



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