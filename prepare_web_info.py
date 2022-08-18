"""
Вспомогательный модуль готовит информацию для
представления на web-странице
"""

import sqlite3
import json
import pprint


def get_web_info():
    """
    Функция возвращает три словаря:

    словарь условий запроса к hh.ru:
    req_dict = {
                {"vac_regs": cписок строк - названий регионов РФ, в которых ищем вакансии
                 "key_words": ключевые слова поиска
                 "days_vac_valid": актуальность вакансии, дней
                 "with_salary": обязательно ли с указанием заработной платы
                 }
    словарь регионов, в которых проводился поиск
    reg_active_dict{'имя региона': код_города_hh}

    словарь результатов поиска
    search_result_dict = {
                 'vac_number': сколько найдено вакансий
                 'sal_max': максимум оплаты по всем полям всех вакансий
                 }
    """
    conn = sqlite3.connect('vac_hh.db')
    cursor = conn.cursor()

    search_result_dict = {}

    # Сколько всего вакансий в базе
    cursor.execute('select id_hh from vacancy')
    search_result_dict['vac_number'] = len(cursor.fetchall())

    # список регионов, в которых проводился поиск вакансий
    cursor.execute('select * from region where in_use =?', (1,))
    reg_active_tuple_lst = cursor.fetchall()

    # формируем словарь регионов, в которых искали вакансии
    reg_active_dict = {'ВСЕ': 0}
    for r in reg_active_tuple_lst:
        reg_active_dict[r[1]] = r[0]

    # узнаем максимальную заработную плату
    #     по столбцам vacancy.s_from и vacancy.s_to
    cursor.execute('select max(max(s_from), max(s_to)) from vacancy')
    search_result_dict['sal_max'] = cursor.fetchone()[0]

    # читаем из файла json условия запроса вакансий
    req_dict = {}
    with open('data/request_dict.json', 'r') as f:
        req_dict = json.load(f)
        f.close()

    # формируем словарь требований к должности
    cursor.execute('select * from skill')
    skill_tuple_lst = cursor.fetchall()

    skill_dict = {'БЕЗ ТРЕБОВАНИЙ': 0}
    for sk in skill_tuple_lst:
        skill_dict[sk[1]] = sk[0]



    # *******  Завершение работы с таблицами   *******
    #    commit the changes to db
    conn.commit()
    #    close the connection
    conn.close()

    return req_dict, reg_active_dict, search_result_dict, skill_dict



def get_vac_info(were_to_find=0, what_skills=0,sal_min=0):
    """
    выдает список словарей-вакансий,
    информация о каждой вакансии усеченная:
        id
        название
        заработная плата
        регион,
        населенный пункт,
        key-skills вакансии (строкой)
        url
    :param: filter - словарь с ограничениями для поиска

    :param were_to_find: код региона для выборки
    :param what_skills: код скил для выборки
    :param sal_min: минимальная заработная плата
    :return: список словарей вакансии
    """

    conn = sqlite3.connect('vac_hh.db')
    cursor = conn.cursor()

    # строим запрос с переменным количеством условий
    req0 = 'select v.id_hh, v.name, r.name, t.name, v.s_from, ' \
          'v.s_to, v.s_currency, v.url from vacancy v, region r, town t ' \
          'where v.area=r.id_hh and v.town=t.id_hh ' \
          'and (v.s_from>=? or v.s_to>=?)'

    if were_to_find and what_skills:
        req = 'select v.id_hh, v.name, r.name, t.name, v.s_from, ' \
              'v.s_to, v.s_currency, v.url, s.name ' \
              'from vacancy v, region r, town t, skill s, vac_skill vs ' \
              'where v.area=r.id_hh and v.town=t.id_hh ' \
              'and (v.s_from>=? or v.s_to>=?) and v.area=? ' \
              'and vs.id_vac=v.id_hh and vs.id_skill=?'
        cursor.execute(req, (sal_min, sal_min, were_to_find, what_skills))
    elif were_to_find:
        req = req0 + ' and v.area=?'
        cursor.execute(req, (sal_min, sal_min, were_to_find))
    elif what_skills:
        req = 'select v.id_hh, v.name, r.name, t.name, v.s_from, ' \
              'v.s_to, v.s_currency, v.url, s.name ' \
              'from vacancy v, region r, town t, skill s, vac_skill vs ' \
              'where v.area=r.id_hh and v.town=t.id_hh ' \
              'and (v.s_from>=? or v.s_to>=?) ' \
              'and vs.id_vac=v.id_hh and vs.id_skill=?'
        cursor.execute(req, (sal_min, sal_min, what_skills))
        pass
    else:
        cursor.execute(req0, (sal_min, sal_min))

    vac_lst = cursor.fetchall()

    # к сожалению, при внедрении в запрос кросс-таблицы vak_skill,
    # появляются повторяющиеся вакансии, и найти причину я не смог.
    # убираем повторяющиеся записи из результата.
    id_lst = [v[0] for v in vac_lst]
    id_lst = set(id_lst)
    id_lst = list(id_lst)
    vac_short_lst = []
    for id in id_lst:
        for vac in vac_lst:
            if vac[0] == id:
                vac_short_lst.append(vac)
                break

    vac_lst = vac_short_lst

    # собираем все данные в список красивых словарей для публикации
    #     получаем все ключевые слова для каждой вакансии
    #     и собираем их в одну строку для последующей публикации
    #     отчета о найденных вакансиях

    # возвращаемый словарь вакансий
    vac_dict_lst = []

    for vac in vac_lst:

        vac_dict={}
        id = vac[0]
        vac_dict['id'] = vac[0]
        vac_dict['name'] = vac[1]
        vac_dict['reg'] = vac[2]
        vac_dict['town'] = vac[3]
        vac_dict['s_from'] = vac[4]
        vac_dict['s_to'] = vac[5]
        vac_dict['cur'] = vac[6]
        vac_dict['url'] = vac[7]

        req = 'select vs.id_vac, s.name ' \
             'from vac_skill vs, skill s ' \
              'where vs.id_skill=s.id and vs.id_vac=?'
        cursor.execute(req, (id,))
        skill_lst = cursor.fetchall()
        # собираем все  skill в строку
        sk_str = '/ '
        for sk in skill_lst:
            sk_str += sk[1]+' / '

        vac_dict['skill'] = sk_str

        vac_dict_lst.append(vac_dict)

    # *******  Завершение работы с таблицами   *******
    #    commit the changes to db
    conn.commit()
    #    close the connection
    conn.close()


    return vac_dict_lst




if __name__ == '__main__':

    v_lst = get_vac_info(were_to_find=0, what_skills=0, sal_min=0)

    print('всего вакансий', len(v_lst))
    pprint.pprint(v_lst)




