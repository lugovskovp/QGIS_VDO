''' Enumerate values in one place '''
import enum

'''
BlockType
en_CARINET_LANGUAGE
en_POI_CAT
en_TeleAtlasRegion
    en_GEO_CATEGORY
    en_DRAW_TYPE
'''

# flake8: noqa E221

@enum.unique
class BlockType(enum.Enum):
    ''' Known block types '''
    ABSTRACT = 0x12
    BIBLIOGR = 0x13
    SCALES = 0x07

    CH_country = 0x0b  # fully parsed chars idxs
    COUNTRY = 0x0a  # fully parsed COUNTRY INFO
    CH_city = 0x0d  # fully parsed chars idxs
    CITY = 0x0c  # fully parsed CITY INFO
    CH_road = 0x0f  # fully parsed chars idxs
    ROAD = 0x0e  #
    CH_poi = 0x11  # fully parsed chars idxs
    POI = 0x10  # fully parsed, POI
    
    SCALE_ALMANAC = 0x08    # set of map folders 0x9.
    FOLDER_MAPS = 0x09		# map folders 0x9.
    MAP__POLI_1 = 0x06  # scale 1
    MAP__POLI_2 = 0x01  # scale 2
    MAP__POLI_3 = 0x02  # scale 3
    MAP__POLI_4 = 0x03  # scale 4
    MAP__05k200 = 0x14  # scale 5   14_MAP_POLI_5_k200	//[5] 5(9:200h)-0x14
    MAP__06k80 = 0x15  	# scale 6   15_MAP_POLI_6_k80	//[6] 6(7:80h)-0x15
    MAP__07k40 = 0x16  	# scale 7   16_MAP_POLI_7_k40	//[7] 7(6:40h)-0x16
    #						#								//[8] - всегда всё 0.
    MAP__09k100 = 0x1c  # scale 9   1c_MAP_POLI_9_k100	//[9]  9(8:100h)-0x1c
    MAP__10k400 = 0x1d  # scale 10  1d_MAP_POLI_10_k400 //[10] a(a:400h)-0x1d
    MAP__11k_11 = 0x1e  # scale 11  1e_MAP_POLI_11			//[11] b(b:666h)-0x1e

    UNKN = 0xFF  # если тип блока ещё не описан

    bl_0x0 = 0x0
    bl_0x4 = 0x4
    bl_0x17 = 0x17
    bl_0x18 = 0x18
    
    # EMPTY = BLOCK_TYPE_EMPTY_ENTRY    # value may be '00 00 00 00' - its legal, but
    # empty, must not read
    # UNKN  = BLOCK_TYPE_UNKNOWN
    # ТИПЫ БЛОКОВ archived by zlib in bmw:
    # 17 1E 09 1D 14 1C 15 16 01 02 03 04 00 06 10 11 0E 0F 0C 0D 0A 13
    # 17 *1E *09 *1D *14 *1C *15 *16 *01 *02 *03
    #  04 00 *06 *10 *11 *0E *0F *0C *0D *0A *13


# Nederlands, English, French, Deutch, Italian, Hispain, Svedian
#!"Nederlands=1, English=2, French=3, Deutch=4, Italian=5, Spanish=6, Swedish=7"
@enum.unique
class en_CARINET_LANGUAGE(enum.Enum):
    noLang = 0
    Holland = 1             # //01 (1) 	 nederland, belgie - Dutch
    English = 2             # //02 (2) 	 united kingdom, eire
    French = 3              # //03 (3) 	 france, luxembourg
    Deutch = 4              # //04 (4) 	 deutschland oesterreich osterreich schweiz
    Italian = 5             # //05 (5) 	 italia
    Spanish = 6             # //06 (6) 	 espana
    Swedish = 7             # //07 (7) 	 sverige
    unk_lang_x08 = 8        #
    unk_lang_x09 = 9        #
    Danian = 0xA            # //0A (10) 	 danmark
    Catalan = 0xB           # //0B (11) 	 andorra
    Finnish = 0xC           # //0C (12) 	 suomen tasavalta
    unk_x0d = 0xD           #
    Norvegian = 0xE         # //0E (14) 	 norge
    Portugal = 0xF          # //0F (15) 	 portugal  //07FF: (nenhuma mensagem)
    unk_lang_x10 = 0x10     # // _english_TOO
    eng_TOO_x11 = 0x11      #
    Polish = 0x12           # //12 (18) 	 polska
    Czech = 0x13            # //13 (19) 	 ceska republika
    Slovak = 0x14           # //14 (20) 	 slovenska republika
    Russian = 0x15          # RUSSIA
    Croatian = 0x1A         # //1A (26) 	 hrvatska
    Latvian = 0x1B          # //1B (27) 	 latvija
    Lithuanian = 0x18       # //18 (24) 	 lietuva
    Slovene = 0x17          # //17 (23) 	 slovenija
    UNKN_FF = 0xFF          #


@enum.unique
class en_POI_CAT(enum.Enum):    	# //{en_PLACE_CATEGORY	 0xA 0xC blocks
    Car_repair        = 0x0B  #
    Gas_station       = 0x0C  #
    CarRent           = 0x0D  #
    Parking           = 0x0E  #
    ParkAndRide       = 0x0F  # // park and ride, intercept parking, parkuj i jedz metro marymont
    RestingPlace      = 0x10  # //  mop olesnica mala,  mop jonas polnoc, mop jonas poludnie
    Intresting        = 0x14  #
    Hotel             = 0x15  #
    Restaurant        = 0x16  #
    Bank              = 0x17  #
    Culture           = 0x18  #
    Library           = 0x19  #
    Court             = 0x1a  #
    UNKN_BMW	      = 0x1C  
    Embassy           = 0x1D  #
    BankomatATM       = 0x1E  #
    Tourist_info      = 0x1F  #
    Museum	          = 0x20  # //musee d'art moderne, musee de l'armee, musee des sciences Naturelles
    Theater           = 0x21  #
    Sport             = 0x23  # //automotodrom brno, o2 arena, ski areal jasna, o2 arena
    Church            = 0x24  #
    Architecture      = 0x25  # //
    Fun_park          = 0x26  # //boudewijn seapark, bruparck
    Nature_park       = 0x27  # //het zwin, nationale plantentuin
    UN_United_Nations = 0x28  # ,
    Hospital          = 0x29  #
    Police            = 0x2A  #
    Goverment         = 0x2B  #
    Post              = 0x2C  #
    Clinic            = 0x2D  #
    Aphoteca          = 0x2E  #
    Shop              = 0x2F  # // supermarket?
    City	          = 0x30  # //russian map
    Cinema            = 0x31  #
    golf_club 	      = 0x32  # //first warsaw golf country club
    RailStation       = 0x33  #
    Border_point      = 0x34  # //
    Seaport           = 0x35  # // oostende ramsgate (tonnel), zeebrugge (port), need mode exmpls
    BusStation        = 0x36  #
    Pier              = 0x37  # // przystan kortowska-> Piers, Dock
    Shcool            = 0x38  #
    Winery            = 0x39  # // lanson caves, champagne krug, moet et chandon, ruinart caves
    Airport           = 0x3a  # //brussel nationaal, brussels airport; , luchthaven brussel
    motorbike_service = 0x3B  # bmw_motorbike_service
    Business          = 0x3D  # // Olsztyn, Poland https://en.wikipedia.org/wiki/Michelin_Polska


'''

 OS-9000/MIPS  V3.0  Copyright (c) 1997-2000 by Microware Systems Corp.
 1991 - 2005 SiemensVDO Automotive AG
 
 
rt3595.img - CT_db_EN.CD 
Road : Town : Curr. loc Archive « » Town halls, town centre Universities, colleges 
Hospitals Hotels Restaurants Vinyards Business centres, industrial sites Shopping, Supermarkets Tradesmen Cult/·
ure, museums, theatres Tourism, historic monuments Shows and exhibitions Casinos and nightlife Cinemas Sports centres Golf cours/Z
es Skating rinks, bowling alleys Winter sports resorts Parks and gardens Theme parks Airports, Ports Stations, bus stations Auto.«
matic checks Vehicle rental Rest areas, car parks Service stations, garages 

TOWN HALLS, TOWN CENTRE UNIVERSITIES, COLLEGES HOSPITALS HOTELS RESTAURANTS VINYARDS BUSINESS CENTRES, INDUSTRIAL SITES 
SHOPPING, SUPERMARKETS TRADESMEN CULTURE, MUSEUMS AND THEATRES TOURISM, HISTOR"ň
IC MONUMENTS SHOWS AND EXHIBITIONS CASINOS AND NIGHTLIFE CINEMAS SPORTS CENTRES GOLF COURSES SKATING RINKS, BOWLING ALLEYS WINTE".
R SPORTS RESORTS PARKS AND GARDENS THEME PARKS AIRPORTS, PORTS STATIONS, BUS STATIONS AUTOMATIC CHECKS VEHICLE RENTAL REST AREAS"
, CAR PARKS SERVICE STATIONS, GARAGES 

DTdb7_EN.CD 
Hotels, Restaurants and Shops Culture, tourism and shows Sports and open air centres Transports and automobile 
Airports, Ports Stations, bus stations Automatic checks Vehicle rental Lay-bys, car parks 
Service stations, garages Hotels Restaurants Vinyards Business centres Shopping, Supermarkets Tradesmen Town halls, town centre 
Universities, colleges Hospitals Sports centres Golf courses Skating rinks, bowling alleys Winter sports resorts Parks, gardens  
Theme parks Tourism, historic monuments Culture, museums, theatres Shows and exhibitions Casinos and nightlife Cinemas 

own halls, town centre Universities, colleges Tourism, historic monuments Shows and exhibitions 
Casinos and nightlife Cinemas Sports centres Golf courses Skating rinks, bowling alleys Winter sports resorts 
Parks and gardens Theme parks Hospitals Airports, Ports Stations, bus stations Automatic checks Vehicle rental Lay-bys, car parks 
Service stations, garages Hotels Restaurants Vinyards Business centres Supermarkets Shopping Culture, museums and theatres 

Universities, colleges Town halls, town centre Hospitals Airports, Ports Vehicle rental 
Service stations, garages Automatic checks Lay-bys, car parks Stations, bus stations Business centres HЇtels  
Restaurants  Shopping, Supermarkets Tradesmen Vinyards Skating rinks, bowling alleys Theme parks Golf courses 
Parks and gardens Sports centres Winter sports resorts Casinos and nightlife Cinemas Culture, museums and theatres 
Shows and exhibitions Tourism, historic monuments

'''


@enum.unique
class en_TeleAtlasRegion(enum.Enum):             # TeleAtlasHexRegion
    SHQIPERIA = 0x02                          # Албания
    ANDORRA = 0x05                            # Андорра
    OESTERREICH = 0x0E                        # Австрия
    AZARBAYCAN = 0x0F                         # Азербайджан
    BYELARUS_BYELARUS = 0x14                  # Беларусь
    BELGIE_BELGIE = 0x15                      # Бельгия
    BOSNA_I_HERCEGOVINA = 0x1B                # Босния и Герцеговина
    BULGARIA = 0x21                           # Болгария
    HRVATSKA = 0x35                           # Хорватия
    KIBRIS = 0x37                             # Кипр
    CESKA_REPUBLIKA = 0x38                    # Чехия
    DANMARK = 0x39                            # Дания
    EESTI_VABARIIK = 0x43                     # Эстония
    SUOMI_SUOMEN_TASAVALTA = 0x48             # Финляндия
    FRANCE = 0x49                             # Франция
    SAKARTVELO = 0x50                         # Грузия
    DEUTSCHLAND = 0x51                        # Германия
    GIBRALTAR = 0x53                          # Гибралтар
    ELLAS_ELLADA = 0x54                       # Греция
    MAGYARORSZAG = 0x61                       # Венгрия
    LYOVELDIO_ISLAND = 0x62                   # Исландия
    EIRE_IRELAND = 0x67                       # Ирландия
    ITALIA = 0x69                             # Италия
    LATVIJA = 0x75                            # Латвия
    LIECHTENSTEIN = 0x7A                      # Лихтенштейн
    LIETUVA = 0x7B                            # Литва
    LUXEMBOURG = 0x7C                         # Люксембург
    MAKEDONIJA = 0x7E                         # Северная Македония
    MOLDOVA = 0x8C                            # Молдова
    MONACO = 0x8D                             # Монако
    NEDERLAND = 0x96                          # Нидерланды
    NORGE = 0xA0                              # Норвегия
    POLSKA = 0xAB                             # Польша
    PORTUGAL = 0xAC                           # Португалия
    ROMANIA = 0xB0                            # Румыния
    ROSSIYA = 0xB1                            # Россия
    SAN_MARINO = 0xB7                         # Сан-Марино
    SLOVENSKO_SLOVENSKA_REPUBLIKA = 0xBE      # Словакия
    SLOVENIJA = 0xBF                          # Словения
    ESPANA = 0xC4                             # Испания
    SVERIGE = 0xCC                            # Швеция
    SCHWEIZ = 0xCD                            # Швейцария
    TURKIYE = 0xD8                            # Турция
    UKRAYINA = 0xDD                           # Украина
    UNITED_KINGDOM = 0xDF                     # Великобритания
    STATO_DELLA_CITTA_DEL_VATICANO = 0xE5     # Ватикан
    SRBIJA_I_CRNA_GORA = 0xF1                 # Сербия и Черногория


@enum.unique
class en_GEO_CATEGORY(enum.Enum):    	#//{en_GEO_OBJ_TYPE	// 03->05->06->08->01->00 blocks MAPS
    """
Rак искать недостающие коды самостоятельно в сети:
Если в процессе парсинга вы наткнетесь на неизвестный байт (например, 0x12 или 0x6F), используйте следующие 
поисковые маркеры в Google, GitHub или специализированных GIS-форумах (вроде GPSPower, Digital-Eliteboard или 
OpenStreetMap Wiki):
::Поиск по спецификациям GDF: Ищите комбинации вида "GDF 4.0" Feature Class codes list или 
"ISO 14825" attribute tables. В официальных PDF-документах ISO (иногда их выкладывают университеты) 
есть полные таблицы маппинга.
::Поиск по исходникам старых конвертеров: На GitHub ищите репозитории по ключевым 
словам "MultiNet" parser, "GDF" converter, или "SDAL" decoding (SDAL — конкурирующий открытый формат от Navteq, 
но логика типов объектов там пересекается).
::OSM Mapping Tables: В википедии OpenStreetMap есть официальные страницы перевода (маппинга) проприетарных карт 
в OSM: ищите "Tele Atlas MultiNet to OSM" table. Там энтузиасты часто публикуют точные таблицы соответствия 
внутренних ID классов Tele Atlas тегам OSM (landuse=forest, highway=motorway).
    """
    """
    Площадные (полигональные) объекты — 'Background layers' (Диапазон 0x00 - 0x3F).
    Используются для заливки фона карты.
    """
    EMPTY = 0x00              # Пустая область / базовый фон суши
    WATER = 0x01              # Внутренние воды (озера, водохранилища, заливы)
    SEA_OCEAN = 0x02          # Моря и океаны
    FOREST = 0x03             # Леса, лесные массивы, густая растительность
    NATIONAL_PARK = 0x04      # Заповедники, национальные парки и заказники
    CITY = 0x05               # Полигон общей жилой застройки города / населенного пункта
    INDUSTRIAL = 0x06         # Промышленные зоны, заводы, склады, порты
    AIRPORT_GROUND = 0x07     # Территория аэропортов (взлетные полосы, терминалы)
    ISLAND = 0x08             # Остров (инвертированный полигон суши внутри воды)
    AMUSEMENT_PARK = 0x09     # Парки развлечений, аттракционы, зоопарки
    GOLF_COURSE = 0x0A        # Поля для гольфа
    CEMETERY = 0x0B           # Кладбища
    HOSPITAL_GROUND = 0x0C    # Территория больниц и медицинских комплексов
    UNIVERSITY_CAMPUS = 0x0D  # Студенческие городки, кампусы вузов
    MILITARY_AREA = 0x0E      # Закрытые военные объекты и полигоны
    SPORTS_COMPLEX = 0x0F     # Спортивные комплексы, открытые стадионы
    """
    Линейные объекты инфраструктуры и гидрографии (Диапазон 0x60 - 0x67, 0x70 - 0x7F).
    Рендерятся линиями без заливки контура.
    """
    CANAL = 0x61              # Искусственные судоходные каналы
    RIVER_STREAM = 0x62       # Узкие реки, ручьи (отображаемые в одну линию)
    RIVER_MAJOR = 0x65        # Основное русло крупной реки
    RAILWAY = 0x66            # Железная дорога
    BORDER = 0x67             # Административные и государственные границы
    PEDESTRIAN_ZONE = 0x70    # Пешеходные дорожки, тротуары, променады
    FERRY_CONNECTION = 0x71   # Линии паромных переправ (виртуальный граф)
    """
    Классификация дорожного графа — Functional Road Classes (Диапазон 0x68 - 0x6F).
    Определяет Z-Index отрисовки дорог и их фильтрацию при масштабировании (LOD).
    """
    ROAD_HIGHWAY = 0x68       # Автомагистрали, автобаны, скоростные трассы (FRC 0)
    ROAD_PRIME = 0x69         # Главные дороги, национальные шоссе, артерии (FRC 1-2)
    ROAD_MINOR = 0x6A         # Второстепенные дороги, межрайонные соединения (FRC 3-4)
    ROAD_LOCAL = 0x6B         # Обычные жилые улицы, внутриквартальные проезды (FRC 5-6)
    ROAD_UNPAVED = 0x6C       # Грунтовые, лесные и полевые дороги (FRC 7)
    ROAD_SLIP = 0x6D          # Съезды с трасс, соединительные ветки развязок (Ramps)
    ROAD_ROUNDABOUT = 0x6E    # Элементы кругового движения (Roundabouts)


@enum.unique
class en_DRAW_TYPE(enum.Enum):    	#//{en_GEO_OBJ_TYPE	// 03->05->06->08->01->00 blocks MAPS
    SHAPE = 0
    POLILINE = 1
