import json
import os
import re
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "banks.json")


class Bank:
    def __init__(self, name, slug, code, nibss_bank_code, country):
        self.name = name
        self.slug = slug
        self.code = code
        self.nibss_bank_code = nibss_bank_code
        self.country = country

    def __repr__(self):
        return f"Bank(name={self.name}, slug={self.slug}, code={self.code}, country={self.country})"


with open(file_path, 'r') as file:
    bank_list = json.load(file)


def find_bank_by_slug(slug):
    bank = next((bank for bank in bank_list if bank['slug'] == slug), None)
    return Bank(**bank) if bank else None

def find_bank_by_code(code):
    bank = next((bank for bank in bank_list if bank['code'] == code), None)
    return Bank(**bank) if bank else None


def get_all_banks():
    return [Bank(**bank) for bank in bank_list]



def is_valid_account_number(value: str) -> bool:
    return re.fullmatch(r"\d{10}", value) is not None

def is_valid_amount(value) -> bool:
    try:
        value = float(value)
        return value >= 200
    except:
        return False
