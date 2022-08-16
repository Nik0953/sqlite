"""
читает данные из файла 'regions.json'
    возвращает словарь: {имя_региона: код_региона}
"""

import json

def get_cities_dict(file_name):
    """
    читает данные из файла 'regions.json'
    возвращает словарь: {имя_региона: код_региона}
    """
    cities_lst = []
    cities_dict = {}
    with open(file_name, 'r') as f:
        cities_lst = json.load(f)

    for town in cities_lst[0]['areas']:
        town_name = str(town['name'])
        cities_dict[town_name] = int(str(town['id']))

    return cities_dict


