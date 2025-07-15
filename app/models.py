from pydantic import BaseModel, Field
from datetime import date

class Person(BaseModel):
    lastname: str = Field(..., example="Гавриченко")
    firstname: str = Field(..., example="Екатерина")
    middlename: str = Field(..., example="Олеговна")
    birthdate: date = Field(..., example="2003-11-26")

class DiplomaData(BaseModel):
    hashed: str = Field(..., example="Иванов Иван Иванович 2005-01-01")
    oa: str = Field(..., example='№5. "Всероссийская олимпиада школьников по физике", 2 уровень. Диплом 1 степени.')
    link: str = Field(..., example="https://diploma.rsr-olymp.ru/files/rsosh-diplomas-static/compiled-storage-2022/by-code/1234567890/white.pdf")
    form: int = Field(..., example=11)
    year: int = Field(..., example=2022)