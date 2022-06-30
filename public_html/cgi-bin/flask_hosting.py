import sys, traceback, json, csv, shutil, pickle, array, re
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
                inputs_cols = ["_QQQ3", "_NQ_F", "_8_38", "_9_00", "_9_00_sq", "_9_26"]
                for key, value in form_dict.items():
                    outputs = value
                    if key in inputs_cols:
                        form_dict[key] = float(value)
            except ValueError:
                message = '{}: 少数点第一位までの数値で入力してください。'.format(outputs)
            # 入力不備あり
            if message is not None:
                form_dict = None

            form_dict["_9_30"] = form_dict["_9_26"]

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

            stats = []
            # 過去の実データを読み込む
            with open('saved_data/stats_{}.csv'.format(html_json['ticker']), newline='', encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)
                sum_criteria = []
                list_csv = list(reader)
                for row in list_csv:
                    row['基準合計'] = ''
                    criteria = re.search(r'^-?\d+', row['基準momemtum'])
                    if criteria:
                        sum_criteria.append(int(criteria[0]))
                        # 10日合計
                        if len(sum_criteria) == 10:
                            row['基準合計'] = str(sum(sum_criteria))
                            sum_criteria = sum_criteria[1:]

                for row in list_csv:
                    if row['QQQ3'] == '':
                        row['_QQQ3'] = '0'
                    else:
                        row['_QQQ3'] = row['QQQ3']
                    if row['Nasdaq100Fut'] == '':
                        row['_NQ_F'] = '0'
                    else:
                        row['_NQ_F'] = row['Nasdaq100Fut']
                    row['_8_38'] = row['8:38']

                    if row['9:00'] == '':
                        row['_9_00'] = '0'
                    else:
                        row['_9_00'] = row['9:00']

                    if row['sq9:00'] == '':
                        row['_9_00_sq'] = '0'
                    else:
                        row['_9_00_sq'] = row['sq9:00']

                    if row['zm9:00'] == '':
                        row['_9_00_zm'] = '0'
                    else:
                        row['_9_00_zm'] = row['zm9:00']

                    row['_9_30'] = row['9:30']
                    if row['9:35'] == '':
                        row['_9_35'] = '0'
                    else:
                        row['_9_35'] = row['9:35']
                    row['_10_00'] = row['10:00']
                    row['_10_45'] = row['10:45']
                    row['_11_30'] = row['11:30']
                    row['_13_30'] = row['13:30']
                    row['_16_00'] = row['16:00']

                    zm_momentum = ''
                    criteria = re.search(r'^-?\d+', row['基準momemtum'])
                    if criteria:
                        zm_momentum = criteria[0]

                    pypl_updown = ''
                    if row['9:00'] != '':

                        if row['_9_35'] != '':
                            if float(row['_9_35']) > float(row['_9_00']):
                                pypl_updown = '(' + '↗︎'
                            elif float(row['_9_35']) == float(row['_9_00']):
                                pypl_updown = '(' + '→'
                            else:
                                pypl_updown = '(' + '↘︎'

                        if row['_10_00'] != '':
                            if float(row['_10_00']) > float(row['_9_35']):
                                pypl_updown = pypl_updown + "↗︎"
                            elif float(row['_10_00']) == float(row['_9_35']):
                                pypl_updown = pypl_updown + '→'
                            else:
                                pypl_updown = pypl_updown + "↘︎"
                            # pypl_updown = pypl_updown + '{:.1f}'.format(float(row['_10_00']) - float(row['_9_00'])) + ") "
                            pypl_updown = pypl_updown + ")"

                    if row['date'] != '':
                        row['date'] = str(int(row['date'][5:7])) + '/' + str(int(row['date'][8:10]))

                    row['date_description'] = '[' + row['date'] + '] ' + row['type'] + '(' + row['AI1'] + ')' + pypl_updown + ' ' + zm_momentum + row['基準'] + ' ' + row['target'] + row['Memo']# + row['基準合計']
                    stats.append(row)

            # 本日のデータを読み込む
            with open('saved_data/saved_form_data.txt', 'r', encoding="utf-8") as data_file:
                json_str = data_file.readlines()
                today_data = json.loads(json_str[0])
                today_data['ticker'] = html_json['ticker']
                today_data['type'] = predicted_type
            today_QQQ3 = float(today_data['_QQQ3'])
            today_NQ_F = float(today_data['_NQ_F'])
            today_8_38 = float(today_data['_8_38'])
            today_9_26 = float(today_data['_9_26'])

            previous = []
            for obj in reversed(stats):
                try:
                    is_append = True
                    if obj['type'] == '':
                        is_append = False
                    elif obj['QQQ3'] == '' or obj['Nasdaq100Fut'] == '':
                        if int(obj['type']) != predicted_type:
                            is_append = False
                    else:
                        penalize = 0
                        if len(obj['target']) > 2:
                            if (today_data['price'] == '高い' and obj['target'][-2:] == '安い') or (today_data['price'] == '安い' and obj['target'][-2:] == '高い'):
                                penalize = 0.1
                                obj['date_description'] = '▲' + obj['date_description']

                        if today_data['type'] != obj['type'][-2:]:
                            penalize = penalize + 0.1
                        else:
                            penalize = penalize - 0.2

                        if today_QQQ3 < -2.5 and float(obj['_QQQ3']) > (-1.0 - penalize):
                            is_append = False
                        elif today_QQQ3 > 2.5 and float(obj['_QQQ3']) < (1.0 + penalize):
                            is_append = False
                        elif float(obj['_QQQ3']) < today_QQQ3 - (1.5 - penalize) or float(obj['_QQQ3']) > today_QQQ3 + (1.5 - penalize):
                            is_append = False

                        if today_NQ_F < -1.0 and float(obj['_NQ_F']) > (-0.5 - penalize):
                            is_append = False
                        elif today_NQ_F > 1.0 and float(obj['_NQ_F']) < (0.5 + penalize):
                            is_append = False
                        elif float(obj['_NQ_F']) < today_NQ_F - (0.5 - penalize) or float(obj['_NQ_F']) > today_NQ_F + (0.5 - penalize):
                            is_append = False

                        if (today_9_26 < today_8_38 and float(obj['_9_00_zm']) > float(obj['_8_38'])) or (today_9_26 > today_8_38 and float(obj['_9_00_zm']) < float(obj['_8_38'])):
                            is_append = False

                        if (today_9_26 < 0 and float(obj['_9_00_zm']) > 0) or (today_9_26 > 0 and float(obj['_9_00_zm']) < 0):
                            is_append = False

                        if obj['_8_38'] != '':
                            if today_8_38 < -1.0 and float(obj['_8_38']) > (-0.5 - penalize):
                                is_append = False
                            elif today_8_38 > 1.0 and float(obj['_8_38']) < (0.5 + penalize):
                                is_append = False
                            elif float(obj['_8_38']) < today_8_38 - (0.5 - penalize) or float(obj['_8_38']) > today_8_38 + (0.5 - penalize):
                                is_append = False

                        if obj['_9_00_zm'] != '':
                            if today_9_26 < -1.0 and float(obj['_9_00_zm']) > (-0.5 - penalize):
                                is_append = False
                            elif today_9_26 > 1.0 and float(obj['_9_00_zm']) < (0.5 + penalize):
                                is_append = False
                            elif float(obj['_9_00_zm']) < today_9_26 - (0.5 - penalize) or float(obj['_9_00_zm']) > today_9_26 + (0.5 - penalize):
                                is_append = False

                    if is_append is True:
                        previous.append(obj)
                except ValueError:
                    # CSV値不備
                    return flask.redirect("/")

            if len(previous) == 0:
                today_data['message'] = '現在パターン別データの不足により表示できません。'
                recent = None
            else:
                recent = previous[0]
            grp_num = len(previous)
            if grp_num > 10:
                grp_num = 10
            return render_template('graph.html', stats=stats, previous=previous, html_json=today_data, recent=recent, grp_num=grp_num)
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

            stats = []
            # 過去の実データを読み込む
            with open('saved_data/stats_{}.csv'.format(html_json['ticker']), newline='', encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)

                sum_criteria = []
                list_csv = list(reader)
                for row in list_csv:
                    row['基準合計'] = ''
                    criteria = re.search(r'^-?\d+', row['基準momemtum'])
                    if criteria:
                        sum_criteria.append(int(criteria[0]))
                        # 10日合計
                        if len(sum_criteria) == 10:
                            row['基準合計'] = str(sum(sum_criteria))
                            sum_criteria = sum_criteria[1:]

                for row in list_csv:
                    if row['QQQ3'] == '':
                        row['_QQQ3'] = '0'
                    else:
                        row['_QQQ3'] = row['QQQ3']
                    if row['Nasdaq100Fut'] == '':
                        row['_NQ_F'] = '0'
                    else:
                        row['_NQ_F'] = row['Nasdaq100Fut']
                    row['_8_38'] = row['8:38']

                    if row['9:00'] == '':
                        row['_9_00'] = '0'
                    else:
                        row['_9_00'] = row['9:00']

                    if row['sq9:00'] == '':
                        row['_9_00_sq'] = '0'
                    else:
                        row['_9_00_sq'] = row['sq9:00']

                    if row['zm9:00'] == '':
                        row['_9_00_zm'] = '0'
                    else:
                        row['_9_00_zm'] = row['zm9:00']
                    row['_9_30'] = row['9:30']
                    if row['9:35'] == '':
                        row['_9_35'] = '0'
                    else:
                        row['_9_35'] = row['9:35']
                    row['_10_00'] = row['10:00']
                    row['_10_45'] = row['10:45']
                    row['_11_30'] = row['11:30']
                    row['_13_30'] = row['13:30']
                    row['_16_00'] = row['16:00']

                    zm_momentum = ''
                    criteria = re.search(r'^-?\d+', row['基準momemtum'])
                    if criteria:
                        zm_momentum = criteria[0]

                    pypl_updown = ''
                    if row['9:00'] != '':

                        if row['_9_35'] != '':
                            if float(row['_9_35']) > float(row['_9_00']):
                                pypl_updown = '(' + '↗︎'
                            elif float(row['_9_35']) == float(row['_9_00']):
                                pypl_updown = '(' + '→'
                            else:
                                pypl_updown = '(' + '↘︎'

                        if row['_10_00'] != '':
                            if float(row['_10_00']) > float(row['_9_35']):
                                pypl_updown = pypl_updown + "↗︎"
                            elif float(row['_10_00']) == float(row['_9_35']):
                                pypl_updown = pypl_updown + '→'
                            else:
                                pypl_updown = pypl_updown + "↘︎"
                            # pypl_updown = pypl_updown + '{:.1f}'.format(float(row['_10_00']) - float(row['_9_00'])) + ") "
                            pypl_updown = pypl_updown + ")"

                    if row['date'] != '':
                        row['date'] = str(int(row['date'][5:7])) + '/' + str(int(row['date'][8:10]))

                    row['date_description'] = '[' + row['date'] + '] ' + row['type'] + '(' + row['AI1'] + ')' + pypl_updown + ' ' + zm_momentum + row['基準'] + ' ' + row['target'] + row['Memo']# + row['基準合計']
                    stats.append(row)

            # 本日のデータを読み込む
            with open('saved_data/saved_form_data.txt', 'r', encoding="utf-8") as data_file:
                json_str = data_file.readlines()
                today_data = json.loads(json_str[0])
                today_data['ticker'] = html_json['ticker']
                today_data['type'] = predicted_type
            today_QQQ3 = float(today_data['_QQQ3'])
            today_NQ_F = float(today_data['_NQ_F'])
            today_8_38 = float(today_data['_8_38'])
            today_9_26 = float(today_data['_9_26'])

            previous = []
            for obj in reversed(stats):
                try:
                    is_append = True
                    if obj['type'] == '':
                        is_append = False
                    elif obj['QQQ3'] == '' or obj['Nasdaq100Fut'] == '':
                        if int(obj['type']) != predicted_type:
                            is_append = False
                    else:
                        penalize = 0
                        if len(obj['target']) > 2:
                            if (today_data['price'] == '高い' and obj['target'][-2:] == '安い') or (today_data['price'] == '安い' and obj['target'][-2:] == '高い'):
                               penalize = 0.1
                               obj['date_description'] = '▲' + obj['date_description']

                        if today_data['type'] != obj['type'][-2:]:
                            penalize = penalize + 0.1
                        else:
                            penalize = penalize - 0.2

                        if today_QQQ3 < -2.5 and float(obj['_QQQ3']) > (-1.0 - penalize):
                            is_append = False
                        elif today_QQQ3 > 2.5 and float(obj['_QQQ3']) < (1.0 + penalize):
                            is_append = False
                        elif float(obj['_QQQ3']) < today_QQQ3 - (1.5 - penalize) or float(obj['_QQQ3']) > today_QQQ3 + (1.5 - penalize):
                            is_append = False

                        if today_NQ_F < -1.0 and float(obj['_NQ_F']) > (-0.5 - penalize):
                            is_append = False
                        elif today_NQ_F > 1.0 and float(obj['_NQ_F']) < (0.5 + penalize):
                            is_append = False
                        elif float(obj['_NQ_F']) < today_NQ_F - (0.5 - penalize) or float(obj['_NQ_F']) > today_NQ_F + (0.5 - penalize):
                            is_append = False

                        if (today_9_26 < today_8_38 and float(obj['_9_00_zm']) > float(obj['_8_38'])) or (today_9_26 > today_8_38 and float(obj['_9_00_zm']) < float(obj['_8_38'])):
                            is_append = False

                        if (today_9_26 < 0 and float(obj['_9_00_zm']) > 0) or (today_9_26 > 0 and float(obj['_9_00_zm']) < 0):
                            is_append = False

                        if obj['_8_38'] != '':
                            if today_8_38 < -1.0 and float(obj['_8_38']) > (-0.5 - penalize):
                                is_append = False
                            elif today_8_38 > 1.0 and float(obj['_8_38']) < (0.5 + penalize):
                                is_append = False
                            elif float(obj['_8_38']) < today_8_38 - (0.5 - penalize) or float(obj['_8_38']) > today_8_38 + (0.5 - penalize):
                                is_append = False

                        if obj['_9_00_zm'] != '':
                            if today_9_26 < -1.0 and float(obj['_9_00_zm']) > (-0.5 - penalize):
                                is_append = False
                            elif today_9_26 > 1.0 and float(obj['_9_00_zm']) < (0.5 + penalize):
                                is_append = False
                            elif float(obj['_9_00_zm']) < today_9_26 - (0.5 - penalize) or float(obj['_9_00_zm']) > today_9_26 + (0.5 - penalize):
                                is_append = False

                    if is_append is True:
                        previous.append(obj)
                except ValueError:
                    # CSV値不備
                    return flask.redirect("/")

            if html_json['message'] == '' and len(previous) == 0:
                today_data['message'] = '現在パターン別データの不足により表示できません。'
                recent = None
            else:
                recent = previous[0]
            grp_num = len(previous)
            if grp_num > 10:
                grp_num = 10
            return render_template('graph.html', stats=stats, previous=previous, html_json=today_data, recent=recent, grp_num=grp_num)

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
