import json
import logging
import re
from datetime import datetime
from typing import List
import asyncio
import httpx
from .models import Person, DiplomaData
from .utils import sha256_hash, build_url, js_to_json, extract_diploma_codes_with_js2py, smart_decode
from .olympiads_mai import OLYMPIADS_BVI_MAI
from .olympiads_mirea import OLYMPIADS_BVI_MIREA
from .olympiads_misis import OLYMPIADS_BVI_MISIS
from .olympiads_bauman import OLYMPIADS_BVI_BAUMAN
from .olympiads_fizteh import OLYMPIADS_BVI_FIZTEH
from .olympiads_mgu import OLYMPIADS_BVI_MGU


logger = logging.getLogger(__name__)

OLYMPIADS_LOOKUP_MAI = None
OLYMPIADS_LOOKUP_MIREA = None
OLYMPIADS_LOOKUP_FIZTEH = None
OLYMPIADS_LOOKUP_MGU = None
OLYMPIADS_LOOKUP_MISIS = None
OLYMPIADS_LOOKUP_BAUMAN = None

def init_olympiads_lookup():
    """Инициализирует lookup-таблицы при запуске приложения"""
    global OLYMPIADS_LOOKUP_MAI, OLYMPIADS_LOOKUP_MIREA, OLYMPIADS_LOOKUP_FIZTEH, \
        OLYMPIADS_LOOKUP_MGU, OLYMPIADS_LOOKUP_MISIS, OLYMPIADS_LOOKUP_BAUMAN

    OLYMPIADS_LOOKUP_MAI = {
        (olympiad["Название олимпиады"], olympiad["Профиль олимпиады"]): True for olympiad in OLYMPIADS_BVI_MAI
    }
    OLYMPIADS_LOOKUP_MIREA = {
        (olympiad["Название олимпиады"], olympiad["Профиль олимпиады"]): True for olympiad in OLYMPIADS_BVI_MIREA
    }
    OLYMPIADS_LOOKUP_MISIS = {
        (olympiad["Название олимпиады"], olympiad["Профиль олимпиады"]): True for olympiad in OLYMPIADS_BVI_MISIS
    }
    OLYMPIADS_LOOKUP_BAUMAN = {
        (olympiad["Название олимпиады"], olympiad["Профиль олимпиады"]): True for olympiad in OLYMPIADS_BVI_BAUMAN
    }
    OLYMPIADS_LOOKUP_FIZTEH = {
        (olympiad["Название олимпиады"], olympiad["Профиль олимпиады"]): True for olympiad in OLYMPIADS_BVI_FIZTEH
    }
    OLYMPIADS_LOOKUP_MGU = {
        (olympiad["Название олимпиады"], olympiad["Профиль олимпиады"]): True for olympiad in OLYMPIADS_BVI_MGU
    }

# Регулярное выражение для парсинга информации об олимпиаде
OA_PATTERN = re.compile(
    r'№(\d+)\.\s*"([^"]+)"\s*\([^"]*"([^"]+)"[^)]*\),\s*(\d+)\s*уровень\.\s*Диплом\s*(\d+)\s*степени\.'
)


def is_valid_for(name: str, speciality: str) -> list:
    univs = []
    for univ_name in [OLYMPIADS_LOOKUP_MAI, OLYMPIADS_LOOKUP_MIREA, OLYMPIADS_LOOKUP_MISIS,
                      OLYMPIADS_LOOKUP_BAUMAN, OLYMPIADS_LOOKUP_FIZTEH, OLYMPIADS_LOOKUP_MGU]:
        if univ_name is None:
            raise RuntimeError("Lookup table not initialized!")
        univs.append((name, speciality) in univ_name)
    return univs

async def fetch_diplomas_for_year(client: httpx.AsyncClient, year: int, person_hash: str) -> List[DiplomaData]:
    url = build_url(year, person_hash)
    try:
        response = await client.get(url, timeout=5)

    except httpx.RequestError as exc:
        logger.error(f"Request failed for {year}: {exc}")
        return []
    if response.status_code == 404:
        return []
    if response.status_code != 200:
        logger.error(f"Error {response.status_code} for {url}")
        return []

    try:
        js_text = smart_decode(response.content)
        raw_data = extract_diploma_codes_with_js2py(js_text)
        diplomas = []
        
        for d in raw_data:
            # Пропускаем дипломы не за 10-11 классы
            if d.get('form') not in (10, 11):
                continue
                
            oa_str = d.get('oa', '')
            match = OA_PATTERN.match(oa_str)
            
            if not match:
                logger.warning(f"Failed to parse oa string: {oa_str}")
                continue
                
            # Извлекаем данные из строки
            olympiad_number = match.group(1)
            olympiad_name = match.group(2)
            olympiad_speciality = match.group(3)
            olympiad_level = int(match.group(4))
            olympiad_result = int(match.group(5))

            univs = is_valid_for(olympiad_name, olympiad_speciality)
            
            diplomas.append(DiplomaData(
                hashed=d.get('hashed'),
                olympiad_name=olympiad_name,
                olympiad_speciality=olympiad_speciality,
                olympiad_level=olympiad_level,
                olympiad_result=olympiad_result,
                link=f"https://diploma.rsr-olymp.ru/files/rsosh-diplomas-static/compiled-storage-{year}/by-code/{d.get('code')}/white.pdf",
                form=d.get('form'),
                year=year,
                valid_mai=univs[0],
                valid_mirea=univs[1],
                valid_misis=univs[2],
                valid_bauman=univs[3],
                valid_fizteh=univs[4],
                valid_mgu=univs[5]
            ))
            
        return diplomas
    except Exception as e:
        logger.error(f"Failed to parse response for year {year}: {e}")
        return []


async def get_all_diplomas(person: Person, years_back: int = 7) -> List[DiplomaData]:
    person_hash = sha256_hash(person)
    current_year = datetime.now().year

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[
            fetch_diplomas_for_year(client, year, person_hash)
            for year in range(current_year, current_year - years_back, -1)
        ])

    return [item for sublist in results for item in sublist]


async def get_diplomas_data(person: Person) -> List[DiplomaData]:
    return await get_all_diplomas(person)
