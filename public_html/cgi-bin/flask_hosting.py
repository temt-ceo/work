import sys, traceback, json, csv, shutil, pickle, array
import flask
from flask import Flask, request, render_template, json
from werkzeug.exceptions import HTTPException
from datetime import date, timedelta
from top_page import show_top_page
from create_csv import do_create_csv
from stats import show_stats

server = Flask(__name__)

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
            return show_top_page(from_page=from_page)
        #
        # Method: POST
        # 分析結果画面
        #
        #
        elif request.method == 'POST':
            form_dict = request.form.to_dict()
            message = None
            outputs = None
            try:
                inputs_cols = ["_8_38", "_9_26", "_9_30"]
                for key, value in form_dict.items():
                    outputs = value
                    if key in inputs_cols:
                        form_dict[key] = float(value)
            except ValueError:
                message = '{}: 少数点第一位までの数値で入力してください。'.format(outputs)
            # 入力不備あり
            if message is not None:
                form_dict = None
            return show_top_page(form_dict=form_dict, message=message)
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
            return do_create_csv(form_dict)

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

@server.route("/stats", methods=['GET', 'POST'])
def stats(html_json=None):
    try:
        #
        # Method: GET
        # 明日以降の動き予測画面
        #
        #
        if request.method == 'GET':
            html_json = {}
            html_json['message'] = ''
            try:
                html_json['today_type'] = int(request.args.get('type'))
            except Exception as e:
                html_json['today_type'] = ''
            return show_stats(html_json=html_json)
        #
        # Method: POST
        # 明日以降の動き予測画面
        #
        #
        elif request.method == 'POST':
            form_dict = request.form.to_dict()
            html_json = {}
            html_json['ticker'] = form_dict['ticker']
            html_json['today_type'] = form_dict['today_type']
            outputs = None
            try:
                inputs_cols = ["_10_00"]
                for key, value in form_dict.items():
                    outputs = value
                    if key in inputs_cols:
                        form_dict[key] = float(value)
            except ValueError:
                html_json['message'] = '{}: 少数点第一位までの数値で入力してください。'.format(outputs)
                form_dict = None
            return show_stats(form_dict=form_dict, html_json=html_json)

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

@server.route("/show_graph", methods=['GET', 'POST'])
def show_graph():
    #
    # Method: GET
    # グラフ表示画面
    #
    #
    if request.method == 'GET':
        try:
            html_json = {}
            html_json['message'] = ''
            if request.args.get('ticker') != 'zm' or request.args.get('type') is None:
                # TOP画面にリダイレクトする
                return flask.redirect("/")
            else:
                html_json['ticker'] = request.args.get('ticker')

            try:
                predicted_type = int(request.args.get('type'))
            except ValueError:
                # getパラメータ改変検知
                return flask.redirect("/")
            
            if predicted_type > 5 or predicted_type < 1:
                # getパラメータ改変検知
                return flask.redirect("/")

            # 本日のデータを読み込む
            with open('saved_data/temp_future.csv', newline='', encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)
                today = date.today()
                tomorrow = today + timedelta(days=1)

                i = 0
                for row in reader:
                    if i == 0:
                        if row['date'] == tomorrow.isoformat(): # 明日以降の動きのデータ(内の昨日のデータ)を参照しているため
                            html_json['today_8_38'] = row['Y8:38']
                            html_json['today_9_26'] = row['Y9:26']
                            html_json['today_9_30'] = row['Y開']
                            _10_00 = (float(row['Y活']) + float(row['Y開'])) / 2
                            html_json['today_10_00'] = '{:.1f}'.format(_10_00)
                        else:
                            # データ未登録のため棒グラフは無し
                            html_json['today_8_38'] = 0
                            html_json['today_9_26'] = 0
                            html_json['today_9_30'] = 0
                            html_json['today_10_00'] = 0
                    i = i + 1

            stats = []
            # 過去の実データを読み込む
            with open('saved_data/stats_{}.csv'.format(html_json['ticker']), newline='', encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)
                for row in reader:
                    row['_8_38'] = row['8:38']
                    row['_9_26'] = row['9:26']
                    row['_9_30'] = row['9:30']
                    row['_9_45'] = row['9:45']
                    row['_10_00'] = row['10:00']
                    row['_10_45'] = row['10:45']
                    row['_11_00'] = row['11:00']
                    row['_11_15'] = row['11:15']
                    row['_11_30'] = row['11:30']
                    row['_12_30'] = row['12:30']
                    row['_13_30'] = row['13:30']
                    row['_16_00'] = row['16:00']
                    stats.append(row)
            previous = []
            for obj in reversed(stats):
                try:
                    if obj['type'] != '' and int(obj['type']) == predicted_type: 
                        previous.append(obj)
                except ValueError:
                    # CSV値不備
                    return flask.redirect("/")

            if len(previous) == 0:
                html_json['message'] = '現在パターン別データの不足により表示できません。'
                recent = None
            else:
                recent = previous[0]
            grp_num = len(previous)
            if grp_num > 9:
                grp_num = 9
            return render_template('graph.html', stats=stats, previous=previous, html_json=html_json, recent=recent, grp_num=grp_num)
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

    #
    # Method: POST
    # グラフ表示画面
    #
    #
    elif request.method == 'POST':
        form_dict = request.form.to_dict()
        try:
            html_json = {}
            html_json['message'] = ''
            if form_dict['ticker'] != 'zm':
                # TOP画面にリダイレクトする
                return flask.redirect("/")

            html_json['ticker'] = form_dict['ticker']

            try:
                predicted_type = int(form_dict['type'])
            except ValueError:
                html_json['message'] = '現在のパターンは1〜5の整数で入力してください。'
                predicted_type = int(form_dict['old_type'])
            
            if predicted_type > 5 or predicted_type < 1:
                html_json['message'] = '現在のパターンは1〜5の整数で入力してください。'

            if html_json['message'] != '':
                predicted_type = int(form_dict['old_type'])

            # 本日のデータを読み込む
            with open('saved_data/temp_future.csv', newline='', encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)
                today = date.today()
                tomorrow = today + timedelta(days=1)

                i = 0
                for row in reader:
                    if i == 0:
                        if row['date'] == tomorrow.isoformat(): # 明日以降の動きのデータ(内の昨日のデータ)を参照しているため
                            html_json['today_8_38'] = row['Y8:38']
                            html_json['today_9_26'] = row['Y9:26']
                            html_json['today_9_30'] = row['Y開']
                            _10_00 = (float(row['Y活']) + float(row['Y開'])) / 2
                            html_json['today_10_00'] = '{:.1f}'.format(_10_00)
                        else:
                            # データ未登録のため棒グラフは無し
                            html_json['today_8_38'] = 0
                            html_json['today_9_26'] = 0
                            html_json['today_9_30'] = 0
                            html_json['today_10_00'] = 0
                    i = i + 1

            stats = []
            # 過去の実データを読み込む
            with open('saved_data/stats_{}.csv'.format(html_json['ticker']), newline='', encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)
                for row in reader:
                    row['_8_38'] = row['8:38']
                    row['_9_26'] = row['9:26']
                    row['_9_30'] = row['9:30']
                    row['_9_45'] = row['9:45']
                    row['_10_00'] = row['10:00']
                    row['_10_45'] = row['10:45']
                    row['_11_00'] = row['11:00']
                    row['_11_15'] = row['11:15']
                    row['_11_30'] = row['11:30']
                    row['_12_30'] = row['12:30']
                    row['_13_30'] = row['13:30']
                    row['_16_00'] = row['16:00']
                    stats.append(row)
            previous = []
            for obj in reversed(stats):
                try:
                    if obj['type'] != '' and int(obj['type']) == predicted_type: 
                        previous.append(obj)
                except ValueError:
                    # CSV値不備
                    return flask.redirect("/")

            if html_json['message'] == '' and len(previous) == 0:
                html_json['message'] = '現在パターン別データの不足により表示できません。'
                recent = None
            else:
                recent = previous[0]
            grp_num = len(previous)
            if grp_num > 9:
                grp_num = 9
            return render_template('graph.html', stats=stats, previous=previous, html_json=html_json, recent=recent, grp_num=grp_num)

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
