import sqlite3
from activate_regions import *

# Создаем базу данных
#     или присоединяемся к созданной
conn = sqlite3.connect('vac_hh.db')

# Создаем курсор
cursor = conn.cursor()

# *******  создаем и заполняем таблицу всех регионов   *******
#    считываем регионы в словарь
city_dict = get_cities_dict('data/regions.json')

#    создаем таблицу регионов
#       name - имя региона
#       code - код региона в hh
#       in_use - является ли регион избранным для анализа вакансий
cursor.execute('create table if not exists region (id integer primary key autoincrement, name varchar (32) unique, code integer unique, in_use boolean default (0) )')

#    заполняем таблицу регионов данными из  regions.json
for city in city_dict:
    cursor.execute('insert into region (name, code) values (?, ?)', (city, city_dict[city]))

#    Избранные города, из которых мы в этот раз хотим получить вакансии:
vac_cities = ['Москва', 'Санкт-Петербург', 'Новосибирская область',
              'Свердловская область', 'Республика Татарстан']

#    Маркируем эти города в таблице:
for city in vac_cities:
    cursor.execute('update region set in_use = 1 where name = ?', (city,))

#    Получаем коды избранных городов
cursor.execute('select code from region where in_use = ?', (1,))
city_tuple_lst = cursor.fetchall()         # список кортежей с кодами на 0-й позиции
city_lst = [x[0] for x in city_tuple_lst]  # просто список кодов избранных городов







# *******  Завершение работы с таблицами   *******
#    commit the changes to db
conn.commit()
#    close the connection
conn.close()
