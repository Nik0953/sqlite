"""
Этот модуль создает базу данных,
запускается однократно.
"""



import sqlite3
from activate_regions import *
from hh_request import *


# ***********   Задаем параметры для запроса в HH.ru     ***********

request_dict = {
    'vac_regs': ['Москва', 'Московская область', 'Санкт-Петербург', 'Ленинградская область', 'Новосибирская область',
              'Свердловская область', 'Республика Татарстан', 'Нижегородская область'],
    'key_words': 'психиатр',
    'days_vac_valid': '3',
    'with_salary': 'true'
}

# --------------------------------------------------------------------


# ***********       Создаем базу данных           ***********

# ***    создаем файл базы или присоединяемся к уже созданной базе   ***
conn = sqlite3.connect('vac_hh.db')

#    Создаем курсор
cursor = conn.cursor()


# ***  создаем и заполняем таблицу регионов   ***

#    считываем регионы в словарь
regions_dict = get_regions_dict('data/regions.json')

#    создаем таблицу регионов
#       id_hh - код региона в hh
#       name - имя региона
#       in_use - является ли регион избранным для анализа вакансий

req_sql = 'create table if not exists region (' \
          'id_hh integer primary key,' \
          ' name varchar (64) unique, ' \
          'in_use boolean default (0))'
cursor.execute(req_sql)

#    заполняем таблицу регионов данными из  regions.json
for reg in regions_dict:
    cursor.execute('insert into region (id_hh, name) values (?, ?)', (regions_dict[reg], reg))

#    Маркируем избранные регионы в таблице:
for reg in request_dict['vac_regs']:
    cursor.execute('update region set in_use = 1 where name = ?', (reg,))

#    Получаем коды избранных регионов
cursor.execute('select id_hh from region where in_use = ?', (1,))
reg_tuple_lst = cursor.fetchall()         # список кортежей с кодами на 0-й позиции
reg_lst = [x[0] for x in reg_tuple_lst]  # просто список кодов избранных регионов

#    считываем нас.пункты в словарь
towns_dict = get_towns_dict('data/regions.json')

# ***   создаем таблицу населенных пунктов   ***
#       id_hh - код нас.пункта в hh
#       name - имя нас.пункта

req_sql = 'create table if not exists town (' \
          'id_hh integer primary key,' \
          ' name varchar (64) unique)'
cursor.execute(req_sql)

#    заполняем таблицу нас.пунктов данными из  regions.json
for t in towns_dict:
    cursor.execute('insert into town (id_hh, name) values (?, ?)', (towns_dict[t], t))


# ***  создаем и заполняем таблицу всех вакансий   ***
#
#    создаем таблицу вакансий
#       hh_id'        id  в head hunter
#       name          название вакансии
#       area          регион
#       s_from        заработная плата от
#       s_to          заработная плата до
#       s_currency    валюта оплаты
#       req           требования
#       resp          обязанности
#       url           ссылка на вакансию
req_sql = 'create table if not exists vacancy ' \
      '(id_hh integer primary key, ' \
      'name varchar (32), ' \
      'area integer references region (id_hh), ' \
      'town integer references town (id_hh), ' \
      's_from  integer, ' \
      's_to integer, ' \
      's_currency varchar (8), ' \
      'req varchar (2048), ' \
      'resp varchar (2048), '\
      'url varchar (256) )'

cursor.execute(req_sql)


#   делаем запрос к hh

vacancy_list = []

for reg in reg_lst:
    print(reg)
    vac_lst = get_vacancies_from_hh(requirements=request_dict['key_words'],
                                    reg=str(reg),
                                    days=request_dict['days_vac_valid'],
                                    salary=request_dict['with_salary'])
    if vac_lst:
        # добавляем в словарь вакансии исходный регион (по которому был запрос)
        for v in vac_lst:
            v['reg'] = reg
        # дописываем вакансии региона reg в общий список
        vacancy_list += vac_lst

print('Всего вакансий:', len(vacancy_list))

#    Запись требований и списка вакансий в файлы

output_file_name = 'data/request_dict.json'
with open(output_file_name, 'w') as f:
    json.dump(request_dict, f, ensure_ascii=False)
    f.close()

output_file_name = 'data/vacancy_list.json'
with open(output_file_name, 'w') as f:
    json.dump(vacancy_list, f, ensure_ascii=False)
    f.close()

# заполняем таблицу вакансий
for v in vacancy_list:
    req_sql = 'insert into vacancy (' \
              'id_hh, ' \
              'name, ' \
              'area, ' \
              'town, ' \
              's_from, ' \
              's_to, ' \
              's_currency, ' \
              'req, ' \
              'resp, ' \
              'url) ' \
              'values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'

    sal_from = None
    sal_to = None
    sal_cur = None

    if v['salary']:
        if v['salary']['from']:
            sal_from = int(v['salary']['from'])
        if v['salary']['to']:
            sal_to = int(v['salary']['to'])
        if v['salary']['currency']:
            sal_cur = v['salary']['currency']

    vac_tuple = (v['id'],
                 v['name'],
                 v['reg'],
                 v['area']['id'],
                 sal_from,
                 sal_to,
                 sal_cur,
                 v['snippet']['requirement'],
                 v['snippet']['responsibility'],
                 v['alternate_url'])
    cursor.execute(req_sql, vac_tuple)


# ***   создаем таблицу ключевых требований   ***
#       id - ключ
#       name - требование (текст)

req_sql = 'create table if not exists skill (' \
          'id integer primary key autoincrement,' \
          ' name varchar (64) unique)'
cursor.execute(req_sql)

skills_lst = ['сертификат', 'нарко', 'лечебное дело',
              'сестринское дело', 'амбулаторн',
              'стационар', 'скор']

#    заполняем таблицу ключевых требований
for sk in skills_lst:
    cursor.execute('insert into skill (name) values (?)', (sk,))


# ***   создаем таблицу связи vacancy и skill   ***
#       id - ключ
#       id_vac из табл. вакансий
#       id_skill - из табл. ключ требований

req_sql = 'create table if not exists vac_skill (' \
          'id integer primary key autoincrement, ' \
          'id_vac integer references vacancy (id_hh), ' \
          'id_skill integer references skill (id))'
cursor.execute(req_sql)


# заполняем таблицу таблицу связи

req_sql = 'INSERT INTO vac_skill(id_vac, id_skill) ' \
          'select v.id_hh, s.id from vacancy v, skill s ' \
          'where (instr(lower(v.req), s.name)>0) or (instr(lower(v.resp), s.name)>0)'
cursor.execute(req_sql)


# *******  Завершение работы с таблицами   *******
#    commit the changes to db
conn.commit()
#    close the connection
conn.close()
