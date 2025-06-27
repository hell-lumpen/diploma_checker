from pydantic import BaseModel, Field
from datetime import date

class Person(BaseModel):
    lastname: str = Field(..., example="Гавриченко")
    firstname: str = Field(..., example="Екатерина")
    middlename: str = Field(..., example="Олеговна")
    birthdate: date = Field(..., example="2003-11-26")

class DiplomaData(BaseModel):
    hashed: str = Field(..., example="Иванов Иван Иванович 2005-01-01")
    olympiad_name: str = Field(..., example="Санкт-Петербургская астрономическая олимпиада")
    olympiad_speciality: str = Field(..., example="астрономия")
    olympiad_level: int = Field(..., example=1)
    olympiad_result: int = Field(..., example=2)
    link: str = Field(..., example="https://diploma.rsr-olymp.ru/files/.../white.pdf")
    form: int = Field(..., example=11)
    year: int = Field(..., example=2022)
    valid_mai: bool = Field(..., example=True)
