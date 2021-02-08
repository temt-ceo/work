import sys, traceback, json, csv, shutil, pickle, array
import flask
from flask import Flask, request, render_template, json
from werkzeug.exceptions import HTTPException
from datetime import date, timedelta
from top_page import show_top_page
import pandas as pd

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
            csv_columns = ["date", "Y開", "Y終", "Y活", "Yx", "Yn", "B5", "Y5", "Px", "Pn", "dis", "B開", "B終", "8:38", "9:26", "flag", "9:30", "活度", "max", "min", "down", "終値", "5日差", "type"]
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
            real_data['Y5'] = real_datas[prev_row]['5日差']
            highest = max(form_data['_9_30'], form_data['_10_00'], form_data['_13_30'], form_data['_16_00'])
            lowest = min(form_data['_9_30'], form_data['_10_00'], form_data['_13_30'], form_data['_16_00'])
            if highest == form_data['_9_30']:
                real_data['Px'] = 1
            elif highest == form_data['_10_00']:
                real_data['Px'] = 2
            elif highest == form_data['_13_30']:
                real_data['Px'] = 3
            elif highest == form_data['_16_00']:
                real_data['Px'] = 4
            if lowest == form_data['_9_30']:
                real_data['Pn'] = 1
            elif lowest == form_data['_10_00']:
                real_data['Pn'] = 2
            elif lowest == form_data['_13_30']:
                real_data['Pn'] = 3
            elif lowest == form_data['_16_00']:
                real_data['Pn'] = 4
            real_data['dis'] = highest - lowest
            real_data['B開'] = real_datas[day2ago]['9:30']
            real_data['B終'] = real_datas[day2ago]['終値']
            real_data['8:38'] = form_data['_8_38']
            real_data['9:26'] = form_data['_9_26']
            real_data['flag'] = form_dict['flag']
            real_data['9:30'] = form_data['_9_30']
            real_data['活度'] = ((int(form_data['_10_00'] * 10) * 2) - int(form_data['_9_30'] * 10)) / 10
            real_data['max'] = form_data['max']
            real_data['min'] = form_data['min']
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
            return show_top_page(from_page=from_page)
        #
        # Method: POST
        # 分析結果画面
        #
        #
        elif request.method == 'POST':
            form_dict = request.form.to_dict()
            return show_top_page(form_dict=form_dict)
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
    try:
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

def show_top_page(form_dict=None, from_page=None):
    today = date.today()
    yesterday = today - timedelta(days=1)

    if form_dict is not None:
        with open('saved_data/saved_form_data.txt', 'r+', encoding="utf-8") as data_file:
            json_str = data_file.readlines()
            html_json = json.loads(json_str[0])
            html_json['date'] = today.isoformat()
            html_json['_8_38'] = form_dict['_8_38']
            html_json['_9_26'] = form_dict['_9_26']
            html_json['_9_30'] = form_dict['_9_30']
            html_json['flag'] = form_dict['flag']
            data_file.truncate(0)
            data_file.seek(0)
            data_file.writelines(json.dumps(html_json))
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
    html_json['pre_16_00'] = real_datas[-1]['終値']
    html_json['pre_vitality'] = real_datas[-1]['活度']
    html_json['pre_highest'] = real_datas[-1]['max']
    html_json['pre_lowest'] = real_datas[-1]['min']
    html_json['_5days_volume'] = real_datas[-1]['5日差']
    # html_json['_5days_diff'] = (int(float(real_datas[-2]['5日差']) * 10) - int(real_datas[-1]['5日差'] * 10)) / 10
    html_json['_5days_diff'] = float(real_datas[-1]['5日差']) - float(real_datas[-2]['5日差'])

    # 予測を行う
    eval_df = pd.read_csv('saved_data/real_data.csv')
    pred_type, real_type = predicting(eval_df)
    html_json['predicted_type'] = pred_type
    html_json['real_type'] = real_type
    html_json['pre_high_pos'] = "9:30"
    html_json['pre_low_pos'] = "16:00"
    html_json['pre_down'] = -4.1
    html_json['pre_high_low_diff'] = 3.2
    # html_json['real_type'] = real_datas[-1]['type']
    html_json['real_high_pos'] = "9:30"
    html_json['real_low_pos'] = "13:30"
    html_json['real_down'] = 0.3
    html_json['real_high_low_diff'] = 1.1

    # Formで入力した情報を予測専用CSVに保存する
    if form_dict is not None:
        html_json['form_submitted'] = True
        real_datas[-1]['date'] = today.isoformat()
        real_datas[-1]['Y開'] = real_datas[-1]['9:30']
        real_datas[-1]['Y終'] = real_datas[-1]['終値']
        real_datas[-1]['Y活'] = real_datas[-1]['活度']
        real_datas[-1]['Yx'] = real_datas[-1]['max']
        real_datas[-1]['Yn'] = real_datas[-1]['min']
        real_datas[-1]['B5'] = real_datas[-2]['5日差']
        real_datas[-1]['Y5'] = real_datas[-1]['5日差']
        real_datas[-1]['Px'] = '' # y値の１つだから使用しない
        real_datas[-1]['Pn'] = ''
        real_datas[-1]['dis'] = ''
        real_datas[-1]['B開'] = real_datas[-1]['Y開']
        real_datas[-1]['B終'] = real_datas[-1]['Y終']
        real_datas[-1]['8:38'] = form_dict['_8_38']
        real_datas[-1]['9:26'] = form_dict['_9_26']
        real_datas[-1]['flag'] = form_dict['flag']
        real_datas[-1]['9:30'] = form_dict['_9_30']
        real_datas[-1]['活度'] = ''
        real_datas[-1]['max'] = ''
        real_datas[-1]['min'] = ''
        real_datas[-1]['down'] = ''
        real_datas[-1]['終値'] = ''
        real_datas[-1]['type'] = ''
        # CSVにデータを登録する
        with open('saved_data/temp.csv', 'w', newline='', encoding="utf-8") as csvfile:
            csv_columns = ["date", "Y開", "Y終", "Y活", "Yx", "Yn", "B5", "Y5", "Px", "Pn", "dis", "B開", "B終", "8:38", "9:26", "flag", "9:30", "活度", "max", "min", "down", "終値", "5日差", "type"]
            writer = csv.DictWriter(csvfile, quoting=csv.QUOTE_ALL, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerow(real_datas[-1])
        eval_df = pd.read_csv('saved_data/temp.csv')
        pred_type, _ = predicting(eval_df, predict_only=True)
        html_json['predicted_today_type'] = pred_type[-1]

    return render_template('index.html', html_json=html_json)

def data_cleaning(df, _type=None):
    if _type is not None:
        df['type'] = _type
    
    # カラム名変更
    for col in df.columns:
        _col = col
        if _type is not None:
            _col = col[2:-1]
        if _col == 'Y開':
            df.rename(columns={col: 'Pre Start'}, inplace=True)
        elif _col == 'Y終':
            df.rename(columns={col: 'Pre End'}, inplace=True)
        elif _col == 'Y活':
            df.rename(columns={col: 'Pre Vitality'}, inplace=True)
        elif _col == 'Yx':
            df.rename(columns={col: 'Pre Max'}, inplace=True)
        elif _col == 'Yn':
            df.rename(columns={col: 'Pre Min'}, inplace=True)
        elif _col == 'B5':
            df.rename(columns={col: '5Days Volume Pre'}, inplace=True)
        elif _col == 'Y5':
            df.rename(columns={col: '5Days Volume'}, inplace=True)
        elif _col == 'Px':
            df.rename(columns={col: 'High Position'}, inplace=True)
        elif _col == 'Pn':
            df.rename(columns={col: 'Low Position'}, inplace=True)
        elif _col == 'dis':
            df.rename(columns={col: 'High Low Diff'}, inplace=True)
        elif _col == 'B開':
            df.rename(columns={col: 'Pre2 Start'}, inplace=True)
        elif _col == 'B終':
            df.rename(columns={col: 'Pre2 End'}, inplace=True)
        elif _col == '8:38':
            df.rename(columns={col: 'PreMarket 838'}, inplace=True)
        elif _col == '9:26':
            df.rename(columns={col: 'PreMarket 926'}, inplace=True)
        elif _col == 'flag_event' or _col == 'flag':
            df.rename(columns={col: 'Alert Level'}, inplace=True)
        elif _col == '9:30':
            df.rename(columns={col: 'Start'}, inplace=True)
        elif _col == '活度':
            df.rename(columns={col: 'Vitality'}, inplace=True)
        elif _col == 'max':
            df.rename(columns={col: 'Max'}, inplace=True)
        elif _col == 'min':
            df.rename(columns={col: 'Min'}, inplace=True)
        elif _col == 'Down' or _col == 'down':
            df.rename(columns={col: 'Avg. Decline'}, inplace=True)
        elif _col == '終値':
            df.rename(columns={col: 'End'}, inplace=True)
    
    for col in df.columns:
        # 数値データの値タイプ変更
        if col == 'Alert Level':
            df[col] = df[col].apply(int)
        else:
            df[col] = df[col].apply(float)

def predicting(eval_df, predict_only=False):
    # カラム数整合用CSVデータを呼び出す
    all_alert_df = pd.read_csv('saved_data/all_alert_data.csv')
    # 評価データにはalert levelが全て含まれていないので含まれているデータとconcat
    df = pd.concat([all_alert_df, eval_df])

    # CSVデータのクリーニング
    df = df[['Y開', 'Y終', 'Y活', 'Yx', 'Yn', 'B5', 'Y5', 'Px', 'Pn', 'dis', 'B開', 'B終', '8:38', '9:26', 'flag', '9:30', '活度', 'max', 'min', 'down', '終値', 'type']]
    eval_df = df.copy()
    data_cleaning(eval_df)

    # 全てのデータは-5~5の範囲にほぼあり、また、0以上と0未満は心理的に重要な意味を持つことからNormalizationは精度が下げる可能性がある為行わない。
    def normalize_x(X):
        # X_norm = (X - X.mean()) / X.std()
        X_norm = X
        return X_norm

    eval_df['Compare 5Days'] = eval_df['5Days Volume'] - eval_df['5Days Volume Pre']
    eval_df.drop('5Days Volume Pre', axis=1, inplace=True)
    def apply_pre_market_pattern(df):
        # 堅調
        if df['PreMarket 926'] > df['PreMarket 838'] + 0.1:
            # 始値でもさらに上昇に転じる
            if df['Start'] > df['PreMarket 926']:
                return 1
            # 始値では下がる
            else:
                return 2
        # 軟調
        elif df['PreMarket 838'] > df['PreMarket 926'] + 0.1:
            # 始値では上昇に転じる
            if df['Start'] > df['PreMarket 926']:
                return 5
            # 始値でもさらに下がる
            else:
                return 6
        # 不定
        else:
            # 始値が上昇する
            if df['Start'] > df['PreMarket 926']:
                return 3
            # 始値が下落する
            else:
                return 4
    eval_df['PreMarket Pattern'] = eval_df.apply(apply_pre_market_pattern, axis=1)
    eval_df.drop('PreMarket 926', axis=1, inplace=True)

    # one hot化
    def preprocess(df):
        # Convert to Bins
        categorical = ['Alert Level', 'PreMarket Pattern']
        
        for column in categorical:
            if column == 'Alert Level':
                one_hot = pd.get_dummies(df[column], prefix=column[:5])
            else:
                one_hot = pd.get_dummies(df[column], prefix=column)
            df = df.drop(column, axis=1)
            df = pd.concat([df, one_hot], axis=1)
        return df
    # 前処理
    preprocessed_df = preprocess(eval_df)
    # 予測に必要となるカラムのみ保持
    X_test = preprocessed_df[['Pre End', 'Pre Vitality', '5Days Volume', 'PreMarket 838', 'Alert_0', 'Alert_1', 'Alert_2', 'Start', 'Compare 5Days', 'PreMarket Pattern_1', 'PreMarket Pattern_2', 'PreMarket Pattern_3', 'PreMarket Pattern_4', 'PreMarket Pattern_5', 'PreMarket Pattern_6']]

    # Y値
    if predict_only is False:
        y_test = preprocessed_df[['type']]
        y_test['type'] = y_test['type'].apply(int)
        real_type = pd.Series(y_test['type'].values).array
    else:
        real_type = None

    # Modelを読み込む
    model = None
    with open('saved_data/model/stock_data_model_v102.pkl', 'rb') as file:
        model = pickle.load(file)

    # 予測
    pred_type = model.predict(X_test)

    return pred_type, real_type

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
