import sys, traceback, json, csv, shutil, pickle
import flask
from flask import Flask, request, render_template, json
from werkzeug.exceptions import HTTPException
from datetime import date, timedelta
# import pandas as pd

server = Flask(__name__)

@server.route("/create_csv", methods=['GET', 'POST'])
def create_csv():
    outputs = None
    try:
        #
        # Method: GET
        # CSVデータ作成画面
        #
        #
        if request.method == 'GET':
            html_json = {}
            html_json['message'] = ''
            return render_template('create_csv.html', html_json=html_json)
        #
        # Method: POST
        # CSVデータ登録画面
        #
        #
        elif request.method == 'POST':
            form_dict = request.form.to_dict()
            today = date.today()
            yesterday = today - timedelta(days=1)
            csv_columns = ["date", "Y開", "Y終", "Y活", "Yx", "Yn", "B5", "B開", "B終", "8:38", "9:26", "flag", "9:30", "活度", "max", "min", "down", "終値", "5日差", "type"]
            inputs_cols = ["type", "_8_38", "_9_26", "_9_30", "_10_00", "_13_30", "_16_00", "max", "min"]

            real_datas = []
            html_json = {}
            html_json['message'] = ''
            form_data = {}
            real_data = {}
            # CSV登録データを呼び出す
            with open('saved_data/real_data.csv', newline='', encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)
                for row in reader:
                    real_datas.append(row)
            # Validation
            if form_dict['ticker'] != 'zm' or yesterday.isoformat() != form_dict['pass']:
                if form_dict['ticker'] != 'zm':
                    html_json['message'] = 'zm以外は現在実装中です。'
                else:
                    html_json['message'] = 'パスコードが一致しません。'
            if real_datas[-1]['date'] == yesterday.isoformat():
                    html_json['message'] = 'すでに直近データは登録済みです。'
            try:
                for key, value in form_dict.items():
                    outputs = value
                    if key in inputs_cols:
                        form_data[key] = float(value)
            except ValueError:
                html_json['message'] = '{}: 少数点第一位までの数値で入力してください。'.format(outputs)
            # 入力不備あり
            if html_json['message'] != '':
                return render_template('create_csv.html', html_json=html_json)

            prev_row = -1
            day2ago = prev_row - 1
            day3ago = prev_row - 2
            day4ago = prev_row - 3
            day5ago = prev_row - 4
            day6ago = prev_row - 5
            # CSV登録データから前日のデータを取得、新規行の入力データに活用する
            real_data['date'] = yesterday.isoformat()
            real_data['Y開'] = real_datas[prev_row]['9:30']
            real_data['Y終'] = real_datas[prev_row]['終値']
            real_data['Y活'] = real_datas[prev_row]['活度']
            real_data['Yx'] = real_datas[prev_row]['max']
            real_data['Yn'] = real_datas[prev_row]['min']
            d1 = int(form_data['_16_00'] * 10)
            d2 = int(float(real_datas[prev_row]['終値']) * 10)
            d3 = int(float(real_datas[day2ago]['終値']) * 10)
            d4 = int(float(real_datas[day3ago]['終値']) * 10)
            d5 = int(float(real_datas[day4ago]['終値']) * 10)
            real_data['B5'] = real_datas[day2ago]['5日差']
            real_data['B開'] = real_datas[day2ago]['9:30']
            real_data['B終'] = real_datas[day2ago]['終値']
            real_data['8:38'] = form_data['_8_38']
            real_data['9:26'] = form_data['_9_26']
            real_data['flag'] = form_dict['flag']
            real_data['9:30'] = form_data['_9_30']
            real_data['活度'] = ((int(form_data['_10_00'] * 10) * 2) - int(form_data['_9_30'] * 10)) / 10
            real_data['max'] = form_data['max']
            real_data['min'] = form_data['min']
            lowest = min(form_data['_9_30'], form_data['_10_00'], form_data['_13_30'], form_data['_16_00'])
            real_data['down'] = (int(lowest * 10) - int(form_data['_9_26'] * 10)) / 10
            real_data['終値'] = form_data['_16_00']
            real_data['5日差'] = (d1 + d2 + d3 + d4 + d5) / 10
            real_data['type'] = int(form_data['type'])
            # バックアップする
            shutil.copyfile('saved_data/real_data_backup.csv', 'saved_data/real_data_backup2.csv')
            # バックアップする(2つ目)
            shutil.copyfile('saved_data/real_data.csv', 'saved_data/real_data_backup.csv')
            # CSVにデータを登録する
            with open('saved_data/real_data.csv', 'w', newline='', encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, quoting=csv.QUOTE_ALL, fieldnames=csv_columns)
                writer.writeheader()
                for row in real_datas:
                    if row['date'] != yesterday.isoformat():
                        writer.writerow(row)
                writer.writerow(real_data)
            # TOP画面にリダイレクトする
            return flask.redirect("/?from_page=create_csv")

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                        limit=2, file=sys.stdout)
        return json.dumps({
            "code": 0,
            "name": "Unexpected Exception",
            "description": "Server Error: {}".format(e),
            "traceback": traceback.format_exc(),
            #"outputs": outputs["_16_00"]
        })
    else:
        pass
    finally:
        pass

@server.route("/", methods=['GET', 'POST'])
def index(html_json=None):
    try:
        #
        # Method: GET
        # 当日データ登録画面
        #
        #
        if request.method == 'GET':
            from_page = request.args.get('from_page')
            return show_top_page(from_page)
        #
        # Method: POST
        # 分析結果画面
        #
        #
        elif request.method == 'POST':
            form_dict = request.form.to_dict()
            if form_dict['ticker'] != 'zm':
                with open('saved_data/saved_form_data.txt', 'r', encoding="utf-8") as data_file:
                    json_str = data_file.readlines()
                    html_json = json.loads(json_str[0])
                return render_template('index.html', html_json=html_json)

            stats = []
            with open('saved_data/saved_form_data.txt', 'r+', encoding="utf-8") as data_file:
                json_str = data_file.readlines()
                html_json = json.loads(json_str[0])
                html_json['t_838'] = form_dict['t_838']
                html_json['t_926'] = form_dict['t_926']
                html_json['y_930'] = form_dict['y_930']
                html_json['y_1000'] = form_dict['y_1000']
                html_json['y_1600'] = form_dict['y_1600']
                html_json['y_lowest'] = form_dict['y_lowest']
                html_json['t_930'] = form_dict['t_930']
                html_json['t_flag'] = form_dict['t_flag']
                today = date.today()
                html_json['date'] = today.strftime("%-m/%d")
                file.truncate(0)
                file.seek(0)
                file.writelines(json.dumps(html_json))
            with open('saved_data/saved_stats.csv', newline='') as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)
                for row in reader:
                    stats.append(row)

            # グラフのbulletの大きさを指定する
            analysis = stats[-1]
            analysis['bullet1'] = abs(float(html_json['t_838']))
            analysis['bullet2'] = abs(float(html_json['t_926']))
            analysis['bulletSquare3'] = abs(float(analysis['early_analyzed_930']))
            analysis['bulletCircle3'] = abs(float(analysis['real_930']))
            analysis['bulletSquare4'] = abs(float(analysis['early_analyzed_1000']))
            analysis['bulletCircle4'] = abs(float(analysis['later_analyzed_1000']))
            analysis['bulletSquare5'] = abs(float(analysis['early_analyzed_lowest']))
            analysis['bulletCircle5'] = abs(float(analysis['later_analyzed_lowest']))

            # 過去10日間の誤差の統計を出す
            for stats_data in stats:
                stats_data['err_930'] = float(stats_data['early_analyzed_930']) - float(stats_data['real_930'])
                stats_data['err_1000'] = float(stats_data['later_analyzed_1000']) - float(stats_data['real_1000'])
                stats_data['err_lowest'] = float(stats_data['later_analyzed_lowest']) - float(stats_data['real_lowest'])
                stats_data['date'] = stats_data['date'][5:].lstrip('0').replace('/0','/')
            return render_template('analyzed_result.html', stats=stats, analysis=analysis, inputs=html_json)

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                        limit=2, file=sys.stdout)
        return json.dumps({
            "code": 0,
            "name": "Unexpected Exception",
            "description": "Server Error: {}".format(e),
            "traceback": traceback.format_exc(),
        })
    else:
        pass
    finally:
        pass

def show_top_page(from_page=None):
    today = date.today()
    yesterday = today - timedelta(days=1)

    # 保存ずみのフォーム入力情報を呼び出す
    with open('saved_data/saved_form_data.txt', 'r', encoding="utf-8") as txt_file:
        json_str = txt_file.readlines()
        html_json = json.loads(json_str[0])

    if from_page == 'create_csv':
        html_json['message'] = 'CSVデータの登録が完了しました。'

    # 保存ずみのフォーム入力情報が古い場合は初期化する
    if html_json['date'] != today.isoformat() and html_json['date'] != yesterday.isoformat():
        html_json['_8_38'] = ''
        html_json['_9_26'] = ''
        html_json['_9_30'] = ''
        html_json['flag'] = 0

    # CSV登録データを呼び出す
    real_datas = []
    with open('saved_data/real_data.csv', newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            real_datas.append(row)

    # CSV登録データの直近データ
    html_json['pre_9_30'] = real_datas[-1]['9:30']
    html_json['pre_16_00'] = real_datas[-1]['終値']
    html_json['pre_vitality'] = real_datas[-1]['活度']
    html_json['pre_highest'] = real_datas[-1]['max']
    html_json['pre_lowest'] = real_datas[-1]['min']
    html_json['_5days_volume'] = real_datas[-2]['5日差']
    html_json['pre2_9_30'] = real_datas[-2]['9:30']
    html_json['pre2_16_00'] = real_datas[-2]['終値']

    # Load from file
    # model = None
    # with open('saved_data/stock_data_model.pkl'), 'rb') as file:
    #     model = pickle.load(file)

    # # Calculate the accuracy score and predict target values
    # score = model.score(Xtest, Ytest)
    # print("Test score: {0:.2f} %".format(100 * score))
    # Ypredict = model.predict(Xtest)

    return render_template('index.html', html_json=html_json)

@server.errorhandler(HTTPException)
def handle_exception(e):
    ### Return JSON instead of HTML for HTTP errors.
    """
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response
    """

if __name__ == "__main__":
    server.run()
