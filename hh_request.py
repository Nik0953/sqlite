import requests
import json


def get_vacancies_from_hh(requirements, reg, salary, days):
    """
    функция Московские вакансии с сайта hh.ru
    за последние сутки
    и возвращает их в виде текстового файла для выдачи через telegram
    :param requirements: текстовая строка с требованиями к должности
    :param reg: числовой код региона
    :param salary: обязательно ли с указанием заработной платы
    :param days: сколько дней назад можно брать публикацию вакансий
    :return: возвращает список вакансий
    """

    DOMAIN = 'https://api.hh.ru/vacancies/'

    vacancy_filter = {'text': requirements,
                      'area': str(reg),
                      'only_with_salary': salary,
                      'period': days,
                      'page': '0'
                      }

    # запрос к hh.ru
    result = requests.get(DOMAIN, params=vacancy_filter)

    # Успешно - 2XX
    print('Код ответа от сервера: ', result.status_code)

    data = result.json()

    # общее количество страниц выдачи
    vac_pages = int(data['pages'])

    # здесь будет полный список вакансий
    vacancy_list = []

    page_current = 0

    # читаем постранично доступные вакансии
    while page_current < vac_pages:
        print('Вакансии, страница', page_current)
        vacancy_filter['page'] = str(page_current)
        result = requests.get(DOMAIN, params=vacancy_filter)
        data = result.json()
        # дописываем список вакансий с последней страницы к полному списку
        vacancy_list += data['items']
        page_current += 1

    print('всего собрано вакансий: ', len(vacancy_list), '\n')

    return vacancy_list
