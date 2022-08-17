"""
При запросе вакансий к hh.ru
не совпают переданный серверу и принятый от него код региона.
Можно передать код субъекта РФ
и получить обратно код населенного пункта.
Структура регионов в hh.ru представлена в виде
многоуровнего графа с ветвями различной глубины.

В этом модуле две функции,
обе функции читают данные из файла 'regions.json'
и возвращают словарь: {имя_региона: код_региона}

get_regions_dict() возвращает крупные регионы -  субъекты РФ
get_towns_dict() возвращает все населенные пункты
                     без учета их положения в иерархии
"""

import json


def get_regions_dict(file_name):
    """
    читает данные из файла 'regions.json'
    возвращает словарь регионов РФ: {имя_региона: код_региона}
    """

    reg_dict = {}
    with open(file_name, 'r') as f:
        reg_lst = json.load(f)
        f.close()

    for reg in reg_lst[0]['areas']:
        reg_name = str(reg['name'])
        reg_dict[reg_name] = int(str(reg['id']))

    return reg_dict


def get_towns_dict(file_name):
    """
    читает данные из файла 'regions.json'
    возвращает словарь всех населенных пунктов: {имя_города: код_города}
    """

    # читаем файл '*.json', как обычный текствовый
    #     и разбираем текст
    with open(file_name, 'r') as f:
        txt = f.read().replace('\n', '')
        f.close()

    # словарь населенных пунктов
    town_dict = {}

    # пытаемся найти участки вида "id":"1234" - это код населенного пункта
    for i in range(1, 9000):
        search_str = '\"id\":\"' + str(i) + '\"'
        pos1 = txt.find(search_str)
        pos2 = pos1 + len(search_str) + 70

        txt_i = ''
        if pos1 > 0:
            # нарезаем короткие строки, где находится наименование
            # от "name":" до "area
            txt_i = txt[pos1:pos2]
            search_str1 = '\"name\":\"'
            search_str2 = '\"area'
            pos1a = txt_i.find(search_str1)
            pos2a = txt_i.find(search_str2)
            if pos1a > 0:
                pos1a += 8
                pos2a -= 2
                txt_name = txt_i[pos1a:pos2a]
                txt_name = txt_name.rstrip().lstrip()
                town_dict[txt_name] = i

    return town_dict


if __name__ == '__main__':
    print(get_regions_dict('data/regions.json'))
    print('*'*120)
    print(get_towns_dict('data/regions.json'))
