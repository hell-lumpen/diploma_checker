import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import Person, DiplomaData
from app.service import get_diplomas_data
from fastapi import HTTPException
from .service import init_olympiads_lookup

app = FastAPI(
    title="Проверка дипломов РСОШ",
    description="Асинхронный API для проверки дипломов на сайте https://diploma.rsr-olymp.ru по ФИО и дате рождения.",
    version="1.0.0",
    contact={
        "name": "Максим",
        "telegram": "@hell_lumpen",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
@app.on_event("startup")
async def startup_event():
    init_olympiads_lookup()

@app.get(
    "/health",
    tags=["Service"],
    summary="Проверка работоспособности API",
    description="Позволяет убедиться, что сервис работает. Возвращает `{status: 'ok'}` при нормальной работе.",
    response_description="Состояние сервиса"
)
async def health_check():
    return {"status": "ok"}

@app.post(
    "/check",
    tags=["Diplomas"],
    summary="Проверка дипломов по ФИО и дате рождения",
    description="""
Проверяет наличие дипломов на сайте https://diploma.rsr-olymp.ru.

Требуется передать ФИО и дату рождения. Если дипломы найдены, возвращается список с деталями.
""",
    response_description="Список найденных дипломов",
    response_model=list[DiplomaData]
)
async def check_diplomas(person: Person):
    diplomas = await get_diplomas_data(person)
    if not diplomas:
        raise HTTPException(status_code=404, detail="No diplomas found")
    return diplomas
