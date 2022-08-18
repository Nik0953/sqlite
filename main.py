from flask import Flask, render_template, request
from prepare_web_info import *

app = Flask(__name__)

#    *****  Страница запросов

@app.route('/', methods=['GET', 'POST'])
def run():
    # получение информации для вывода на сайт
    req, reg, s_res, sk = get_web_info()

    if request.method == 'POST':
        # Получть данные формы
        req_form = {}
        req_form['were_to_find'] = int(request.form['where_to_find'])
        req_form['what_skills'] = int(request.form['what_skills'])
        req_form['sal_min'] = int(request.form['sal_min'])

        # словарь для размещения на web странице
        req_web = {}
        req_web['were_to_find'] = [s for s in reg if int(reg[s])==req_form['were_to_find']][0]
        req_web['what_skills'] = [s for s in sk if int(sk[s])==req_form['what_skills']][0]
        req_web['sal_min'] = req_form['sal_min']
        print(req_web)

        v_lst = get_vac_info(were_to_find=req_form['were_to_find'],
                             what_skills=req_form['what_skills'],
                             sal_min=req_form['sal_min'])

        return render_template('results.html', vl=v_lst, rf=req_web)

    elif request.method == 'GET':
        # выводим  html с формой запроса
        return render_template('req.html', regions_dict=reg, req=req, s_res=s_res, skill_dict=sk )

@app.route("/results/")
def results():
    pass
    return render_template('results.html')


if __name__ == "__main__":
    app.run(debug=True)