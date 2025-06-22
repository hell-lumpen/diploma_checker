import hashlib
from .models import Person
import js2py


def sha256_hash(person: Person) -> str:
    namestring = f"{person.lastname} {person.firstname} {person.middlename} {person.birthdate}"
    return hashlib.sha256(namestring.encode()).hexdigest()


def build_url(year: int, hashed_person: str) -> str:
    return f"https://diploma.rsr-olymp.ru/files/rsosh-diplomas-static/compiled-storage-{year}/by-person-released/{hashed_person}/codes.js"

import re

def js_to_json(js_text: str) -> str:
    match = re.search(r"diplomaCodes\s*=\s*(\[\s*{.*?}\s*]);", js_text, re.DOTALL)
    if not match:
        raise ValueError("Array not found in JS")

    array_text = match.group(1)

    array_text = array_text.replace("'", '"')

    array_text = re.sub(r'([{,])\s*(\w+)\s*:', r'\1 "\2":', array_text)

    return array_text

def extract_diploma_codes_with_js2py(js_text: str) -> list[dict]:
    try:
        context = js2py.EvalJs()
        context.execute(js_text)
        result = context.diplomaCodes.to_list()
        return result
    except Exception as e:
        logger.exception(f"Failed to extract with js2py: {e}")
        raise

import chardet

def smart_decode(content: bytes) -> str:
    result = chardet.detect(content)
    encoding = result["encoding"] or "utf-8"
    return content.decode(encoding, errors="replace")
