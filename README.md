
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-brightgreen.svg)](https://www.python.org/downloads/)
[![GitHub License](https://img.shields.io/github/license/lugovskovp/QGIS_VDO)](#)
[![Format: CARINdb](https://img.shields.io/badge/format-CARiN%20%2F%20CarinDB-orange.svg)](https://github.com/fdemusso/OpenCarin)
![Coverage](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Flugovskovp%2Fd73b601c90fe3a20bf364ee079c4a5c3%2Fraw%2Fqgis_vdo_coverage.json)
![GitHub Issues](https://img.shields.io/github/issues/lugovskovp/QGIS_VDO)
![GitHub Release](https://img.shields.io/github/v/release/lugovskovp/QGIS_VDO?link=https%3A%2F%2Fgithub.com%2Flugovskovp%2FQGIS_VDO%2Freleases%2Flatest)





# About
Systeme Guidage Carminat C-IQ navigation database QGIS viewer This plugin for view/explore a digital road map database for the CARiN- and VDODayton navigation compatible systems

Плагин для просмотра в QGIS данных файлов навигационных систем VDO Dayton CD, устанавливавшихся на Citroen, Pegout, BMW, Mercedes, Fiat ect с начала 2000 годов.
Формат карт для CARiN называется CDF (CARiN Database Format).

> [!IMPORTANT]  
> Плагин в процессе разработки, релиз v.1 по факту beta, рекомендуется ожидать версии 2.x.x.

[![image](https://github.com/user-attachments/assets/7869eaa4-c747-43bc-b7ad-f6657638ce1f)](https://github.com/user-attachments/assets/7869eaa4-c747-43bc-b7ad-f6657638ce1f)

# Версии ПО
Оригинальная ОС система автонавигатора OS-9000/MIPS  V3.0  Copyright (c) 1997-2000 by Microware Systems Corp.
1991 - 2005 SiemensVDO Automotive AG
 
- QGIS 3.44.10 ltr
- VDO Dayton CD Carindb v.30
- VDO Dayton CD Carindb v.34

- ~pip install bitarray~ - только для дебага и разработки


# Функциональность
- [x] Выбор файла. Вывод инфо о файле (файлах). Запоминание настроек.
- Выбор страны, города, дороги, точки интереса вводом адреса
- Отображение категорий POI, вывод списка категорий и POI по ним в интерфейс QGIS
- [x] Отображение картографического слоя по масштабам
- [x] Работа с несколькими carindb
- [x] Отображение в пользовательской СК "WGS 84 / Custom Pacific Split -80" - линия разрыва в атлантике, 80W

## CI ограничения разработки
- ci запрет: коммит при синтаксических ошибках - flake8
- ci запрет: коммит при непрохождении любого из автотестов (на 2026-09-18 их 444, 2026-10-14: 570 )
- ci запрет: коммит напрямую в ветку main
- semantic versioning
- при доработке функций блоков **крайне желательно** поддерживать ранее достигнутый уровень покрытия тестами


# История реверс-инжиниринга формата carindb
Формат данных закрытый, история получения информации по значению данных в файлах VDO Dayton на Habr:
- [Реверс черного тессеракта. Начало](https://habr.com/ru/post/597625/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.2f5d74b3-63ff776e-440b408c-74722d776562/https/habr.com/ru/post/597625/)
- [01. Сшей красное с красным, желтое с желтым, белое с белым. Наверняка будет хорошо](https://habr.com/ru/post/597851/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.1f39f163-63ff7879-fca36fdd-74722d776562/https/habr.com/ru/post/597851/)
- [02. Я уже даже не вижу код. Я вижу блондинку, брюнетку и рыжую](https://habr.com/ru/post/598673/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.7eefa2d2-63ff78ae-7b1bd31b-74722d776562/https/habr.com/ru/post/598673/)
- [03. С прозрачными воротами и яркою звездой](https://habr.com/ru/post/599661/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.feff4f4f-63ff7b3d-64ac638b-74722d776562/https/habr.com/ru/post/599661/)
- [04. The Gold-Bug](https://habr.com/ru/post/645355/) [eng](https://translated.turbopages.org/proxy_u/ru-en.ru.65863e91-63ff7baa-91e5cf05-74722d776562/https/habr.com/ru/post/645355/)
- i hope to be continued...



