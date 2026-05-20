""" Типы данных для карт - БЛОКОВ
    bmw ee bnl:  00 16 15 1c 14 1d 1e
        future: MAP_AREA(BYTESTRUCT):
        future: POI_CATEGORY

COORD
functions:
    hex2COORD
    float2COORD
    str2COORD
    normLatLng
"""

import re

from vdo.datatypes import BYTESTRUCT
from vdo.datatypes import DOUBLE_BYTES_CNT, UINT_struct

# на столько делится 1°00′
# 1 градус экватора = 111362м / 5555554 = 0,02м - цена меньшего бита 2cm
MULCOORD = 0x54C563     # dec 5555555 - волшебный коэффициент перевода.
                        
MOST_SIGNIFICANT_BIT = 0x80000000  # hi bit =1 -> minus val.


class COORD(BYTESTRUCT):
    """ coordinates, 2 dwords: lon lat """
    #_lon: float         # double lon = ((1.0f * hlon )/ MULCOORD) - 30.0;
    #_lat: float         # double lat = 1.0f * hlat / MULCOORD;
    _hlon: int
    _hlat: int
       
    size: int = DOUBLE_BYTES_CNT     # 2*DWORD: lon lat

    def __init__(self, buffer: bytearray) -> None:
        """ """

        # === bytearray
        super().__init__(buffer[:DOUBLE_BYTES_CNT])   # 8 - self.size

        self._hlon = UINT_struct.unpack(self._raw[:4])[0]
        self._hlat = UINT_struct.unpack(self._raw[4:8])[0]
        if MOST_SIGNIFICANT_BIT & self._hlon:     # hi bit =1 -> minus val.
            # self.hlo = ctypes.c_int32(self._hlon).value
            self._hlon = 0 - (0xffffffff - self._hlon + 1)
        if MOST_SIGNIFICANT_BIT & self._hlat:     # hi bit =1 -> minus val.
            # self.hla = ctypes.c_int32(self._hlat).value
            self._hlat = 0 - (0xffffffff - self._hlat + 1)
        self.lon = (self._hlon / MULCOORD) - 30     # e/w
        self.lat = self._hlat / MULCOORD            # n/s

        return
        # FFFFFFF = 268435455, / 180 = 1degree = 1491308 (16C16C)=
        # MULCOORD = 0x54C563 # dec 5555554;
        # *90 = 2FAF07B0, *180 = 5F5E0F60,  *180=BEBC1EC0
        # 1 градус экватора = 111362м / 5555554 = 0,02м - цена меньшего бита 2cm
        # 5555554 / 111362м = 49,88734038540974 - в одном метре

    def __repr__(self):
        ''' View while debug value'''
        ch_lat = 'N' if self.lat >= 0 else 'S'
        ch_lon = 'E' if self.lon >= 0 else 'W'
        return "{:02.6f}{:s} {:02.6f}{:s}".format(abs(self.lat),
                                                  ch_lat, abs(self.lon),
                                                  ch_lon)


# -------------------------------------------------------------------------
# functions
# -------------------------------------------------------------------------

def hex2COORD(hex_longtude: int, hex_latitude: int) -> COORD:
    ''' Ret COORD by hex_vdo values lo&la'''
    res: COORD
    hex_latitude = 0xffffffff & hex_latitude    # to dword
    if hex_latitude < 0:                        # Negative val
        hex_latitude = 0x80000000 | (-hex_latitude)
       
    hex_longtude = 0xffffffff & hex_longtude    # to dword
    if hex_longtude < 0:                        # Negative val
        hex_longtude = 0x80000000 | (-hex_longtude)

    coo_by = (UINT_struct.pack(">L", hex_longtude)
              + UINT_struct.pack(">L", hex_latitude))
    res = COORD(coo_by)
    '''    #int DWORD со знаком в старшем бите
    if 0x80000000 & self._hlon:     # hi bit =1 -> minus val.
        self._hlon = 0 - (0xffffffff - self._hlon + 1)
    if 0x80000000 & self._hlat:     # hi bit =1 -> minus val.
        self._hlat = 0 - (0xffffffff - self._hlat + 1)    '''
    return res


def str2COORD(lon_lat: str) -> tuple:
    '''Координаты по строке, lon где E|W, lat-N|S, exmpl: 73.920441N 54.297287E
    Args:
        lon_lat: str  # Широта, latitude и Долгота, longtitude  градусы
    Returns:
        coordinates: tuple(N_lat: hlat, E_lng: hlon)
    '''
        
    # lon_lat - типа 73.92N 54.30E, разделитель - пробел
    # вычистить мусор

    lon_lat = re.sub(r'\s+', ' ', lon_lat)      # remove multispaces
    lon_lat = re.sub(r',\s', ' ', lon_lat)      # remove ', ' between digits
    lon_lat = re.sub(r',', '.', lon_lat)        # . in digits instead ,
    splted = lon_lat.split(' ')
    # две части?
    if len(splted) != 2:
        raise TypeError(f"В строке {lon_lat} координаты не распознаны")
    # разбираемся - где долгота, где широта
    for k in splted:
        if re.search(r'[NnSs]$', k):         # последняя буква - север или юг
            lat = float(re.sub(r'[NnSs]$', '', k))
            if re.search(r'[Ss]', k):
                lat = -lat
        elif re.search(r'[EeWw]$', k):         # последняя буква - восток или запад
            lon = float(re.sub(r'[EeWw]$', '', k))
            if re.search(r'[Ww]', k):
                lon = -lon
        else:
            raise TypeError(f"В строке {lon_lat} должны быть N (или S) и E (или W)")
    # вернуть координаты
    res = float2COORD(lat, lon)
    return res


def float2COORD(n_latitude: float, e_longtude: float) -> tuple:
    ''' Координаты в градусах (широта, долгота)
    Args:
        n_latitude: float   # Широта, latitude градусы
        e_longtude: float   # Долгота, longtitude градусы
    Returns:
        coordinates: tuple(N_lat: hlat, E_lng: hlon)
        '''
    res: COORD
    lat, lon = normLatLng(n_latitude, e_longtude)
    hlon = int((lon + 30) * MULCOORD)   # self._lon = ( self._hlon / MULCOORD ) - 30
    hlat = int(lat * MULCOORD)          # self._lat =   self._hlat / MULCOORD
    res = hex2COORD(hlon, hlat)
    return res


def normLatLng(n_latitude: float, e_longtude: float):
    ''' Нормализует координаты в градусах (широта, долгота)
        возвращает нормализованные (N_lat, E_lng)
    Args:
        n_latitude: float   # Широта, latitude градусы
        e_longtude: float   # Долгота, longtitude градусы
    Returns:
        coordinates: tuple(N_lat: float, E_lng: float)
    '''
    # избавление от кратности круга (370 = 10), КРОМЕ ЭТОГО ПЕРЕВОД В -110 % 360 = 250
    E_lng = float(e_longtude) % 360
    N_lat = float(n_latitude) % 360
    # При переходе в противоположное полушарие широты, долгота +=180
    if 90 < N_lat < 270:     # II and III quadrant.
        # 100N = 80N     # Долгота, longtitude 0 -> 90 -> 0-> -90 -> 0
        N_lat = 180 - n_latitude
        # перепрыг в иное полушарие
        E_lng += 180
    # избавление от кратности круга (370 = 10)
    N_lat = float(N_lat) % 360
    E_lng = float(E_lng) % 360
    # N-S, E-W
    E_lng = E_lng - 360 if E_lng > 180 else E_lng      # 270E = 90W = -90E; 190E = -170E
    N_lat = N_lat - 360 if N_lat > 180 else N_lat      # 350N = -10N
    return (N_lat, E_lng)

# -------------------------------------------------------------------------


if __name__ == '__main__':

    #
    a1 = b'\x06\xe6y\xaa\x0b\xb1\xde\x1f'
    a2 = b'\nlvM\x10_\xf3\xf9'
    a3 = b'(\xc7\xb2\xb8\x17)\x94p'
    a4 = b'\x0cS\xbd\xcb\x11\xb7\x02='

    c1 = COORD(a1)  # 35.317104N 9.161808W
    c2 = COORD(a2)  # 49.450295N 1.478463E
    c3 = COORD(a3)  # 69.948177N 93.151702E
    c4 = COORD(a4)  # 53.497145N 7.226644E

    # import ctypes
    # dword_val = ctypes.c_int32(0xFFFFFFFF).value
    # print(dword_val)    # Выведет: -1
    pass

# import ctypes

# # Приведение к 32-битному знаковому целому
# dword_val = ctypes.c_int32(0xFFFFFFFF).value
# print(dword_val) # Выведет: -1
