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



logger = logging.getLogger(__name__)

OLYMPIADS_LOOKUP_MAI = None


def init_olympiads_lookup():
    """Инициализирует lookup-таблицы при запуске приложения"""
    global OLYMPIADS_LOOKUP_MAI
    OLYMPIADS_LOOKUP_MAI = {
        (olympiad["Название олимпиады"], olympiad["Профиль олимпиады"]): True for olympiad in OLYMPIADS_BVI_MAI
    }

# Регулярное выражение для парсинга информации об олимпиаде
OA_PATTERN = re.compile(
    r'№(\d+)\.\s*"([^"]+)"\s*\([^"]*"([^"]+)"[^)]*\),\s*(\d+)\s*уровень\.\s*Диплом\s*(\d+)\s*степени\.'
)


def is_valid_for_mai(olympiad_name: str, speciality: str) -> bool:
    """Проверяет, учитывается ли олимпиада в МАИ"""
    for olympiad in OLYMPIADS_BVI_MAI:
        if (olympiad["Название олимпиады"] == olympiad_name and 
            olympiad["Профиль олимпиады"] == speciality):
            print("олимпиада в МАИ валидна")
            return True
    print("олимпиада в МАИ не валидна")
    return False

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
            if d.get('form') not in (10, 11):
                continue
            if d.get('hashed') is None or d.get('oa') is None or d.get('form') is None:
                continue
            oa_str = d.get('oa', '')
            match = OA_PATTERN.match(oa_str)
            if not match:
                logger.warning(f"Failed to parse oa string: {oa_str}")
                continue
            olympiad_name = match.group(2)
            olympiad_speciality = match.group(3)
            if not is_valid_for_mai(olympiad_name, olympiad_speciality):
                continue
            diplomas.append(DiplomaData(
                hashed=str(d.get('hashed')),
                oa=str(d.get('oa')),
                link=f"https://diploma.rsr-olymp.ru/files/rsosh-diplomas-static/compiled-storage-{year}/by-code/{d.get('code')}/white.pdf",
                form=d['form'],
                year=year
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
    rows = await get_all_diplomas(person)
    return [DiplomaData(hashed=row.hashed, oa=row.oa, link=row.link, form=row.form, year=row.year) for row in rows]
