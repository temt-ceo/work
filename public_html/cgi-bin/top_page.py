import sys, traceback, json, csv, shutil, pickle, array
import flask
from flask import Flask, request, render_template, json
from werkzeug.exceptions import HTTPException
from datetime import date, timedelta
import pandas as pd


def show_top_page(form_dict=None, from_page=None, message=None):
    today = date.today()
    yesterday = today - timedelta(days=1)
    html_json = {}

    if form_dict is not None:
        with open('saved_data/saved_form_data.txt', 'r+', encoding="utf-8") as data_file:
            json_str = data_file.readlines()
            html_json = json.loads(json_str[0])
            html_json['date'] = today.isoformat()
            html_json['_QQQ3'] = form_dict['_QQQ3']
            html_json['_NQ_F'] = form_dict['_NQ_F']
            html_json['_8_38'] = form_dict['_8_38']
            html_json['_9_00'] = form_dict['_9_00']
            html_json['_9_00_sq'] = form_dict['_9_00_sq']
            html_json['_9_26'] = form_dict['_9_26']
            html_json['_9_30'] = form_dict['_9_30']
            html_json['price'] = form_dict['price']
            if 'early_check' in form_dict:
                html_json['early_check'] = form_dict['early_check']
            else:
                html_json['early_check'] = ''
            data_file.truncate(0)
            data_file.seek(0)
            data_file.writelines(json.dumps(html_json))
    # 保存ずみのフォーム入力情報を呼び出す
    with open('saved_data/saved_form_data.txt', 'r', encoding="utf-8") as txt_file:
        json_str = txt_file.readlines()
        html_json = json.loads(json_str[0])

    if from_page == 'create_csv':
        html_json['message'] = 'CSVデータの登録が完了しました。'
    if message is not None:
        html_json['message'] = message

    # 保存ずみのフォーム入力情報が古い場合は初期化する
    if html_json['date'] != today.isoformat() and html_json['date'] != yesterday.isoformat():
        html_json['_QQQ3'] = ''
        html_json['_NQ_F'] = ''
        html_json['_8_38'] = ''
        html_json['_9_00'] = ''
        html_json['_9_00_sq'] = ''
        html_json['_9_26'] = ''
        html_json['_9_30'] = ''
        html_json['price'] = 0
        html_json['early_check'] = ''

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
    html_json['_5days_diff'] =  '{:.1f}'.format(float(real_datas[-1]['5日差']) - float(real_datas[-2]['5日差']))

    # 予測を行う
    eval_df = pd.read_csv('saved_data/real_data.csv')
    # パターンの予測
    pred_type, real_type = predicting(eval_df[-1:], 'type')
    html_json['predicted_type'] = pred_type[-1]
    html_json['real_type'] = real_type[-1]
    # 高値の位置予測
    eval_df['type'] = pd.Series([pred_type])
    pred_hpos, real_hpos = predicting(eval_df[-1:], 'High Position')
    pos_to_time = list(zip([1,2,3,4],['9:30','10:00','13:30','16:00']))
    html_json['pre_high_pos'] = pos_to_time[pred_hpos[-1] - 1][1]
    html_json['real_high_pos'] = pos_to_time[real_hpos[-1] - 1][1]

    # Formで入力した情報から今日の動きを予測する
    if form_dict is not None:
        html_json = predict_today_result(form_dict, html_json, real_datas)
        html_json['message'] = '今日の予測結果が表示されました。'
        html_json['message2'] = 'グラフ表示のリンクが有効化されました。'
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

def predicting(eval_df, target, predict_only=False):
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
        categorical = None
        if target == 'type':
            categorical = ['Alert Level', 'PreMarket Pattern']
        else:
            categorical = ['Alert Level', 'PreMarket Pattern', 'type']
        
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
    X_test = preprocessed_df[len(all_alert_df):][['Pre End', 'Pre Vitality', '5Days Volume', 'PreMarket 838', 'Alert_0', 'Alert_1', 'Alert_2', 'Start', 'Compare 5Days', 'PreMarket Pattern_1', 'PreMarket Pattern_2', 'PreMarket Pattern_3', 'PreMarket Pattern_4', 'PreMarket Pattern_5', 'PreMarket Pattern_6']]

    # Y値
    if predict_only is False:
        y_test = preprocessed_df[len(all_alert_df):][[target]]
        y_test[target] = y_test[target].apply(int)
        real_type = pd.Series(y_test[target].values).array
    else:
        real_type = None

    # Modelを読み込む
    model = None
    if target == 'type':
        with open('saved_data/model/stock_data_model_v102.pkl', 'rb') as file:
            model = pickle.load(file)
    elif target == 'High Position':
        with open('saved_data/model/stock_data_model_rf_highpos.pkl', 'rb') as file:
            model = pickle.load(file)

    # 予測
    pred_type = model.predict(X_test)

    return pred_type, real_type

def predict_today_result(form_dict, html_json, real_datas):
    today = date.today()
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
    real_datas[-1]['B開'] = real_datas[-2]['Y開']
    real_datas[-1]['B終'] = real_datas[-2]['Y終']
    real_datas[-1]['8:38'] = form_dict['_8_38']
    real_datas[-1]['9:26'] = form_dict['_9_26']
    real_datas[-1]['flag'] = 0 # form_dict['flag']
    real_datas[-1]['9:30'] = form_dict['_9_30']
    real_datas[-1]['活度'] = ''
    real_datas[-1]['max'] = ''
    real_datas[-1]['min'] = ''
    real_datas[-1]['down'] = ''
    real_datas[-1]['終値'] = ''
    real_datas[-1]['5日差'] = ''
    real_datas[-1]['type'] = ''
    # CSVにデータを登録する
    with open('saved_data/temp.csv', 'w', newline='', encoding="utf-8") as csvfile:
        csv_columns = ["date", "Y開", "Y終", "Y活", "Yx", "Yn", "B5", "Y5", "Px", "Pn", "dis", "B開", "B終", "8:38", "9:26", "flag", "9:30", "活度", "max", "min", "down", "終値", "5日差", "type"]
        writer = csv.DictWriter(csvfile, quoting=csv.QUOTE_ALL, fieldnames=csv_columns)
        writer.writeheader()
        writer.writerow(real_datas[-1])
        if html_json['early_check'] == 'checked':
            # 堅調・上昇
            real_datas[-1]['9:26'] = '{:.1f}'.format(float(form_dict['_8_38']) + 0.3)
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_8_38']) + 0.9)
            writer.writerow(real_datas[-1])
            # 堅調・下落
            real_datas[-1]['9:26'] = '{:.1f}'.format(float(form_dict['_8_38']) + 0.3)
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_8_38']) - 0.9)
            writer.writerow(real_datas[-1])
            # 不定・上昇
            real_datas[-1]['9:26'] = '{:.1f}'.format(float(form_dict['_8_38']))
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_8_38']) + 0.9)
            writer.writerow(real_datas[-1])
            # 不定・下落
            real_datas[-1]['9:26'] = '{:.1f}'.format(float(form_dict['_8_38']))
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_8_38']) - 0.9)
            writer.writerow(real_datas[-1])
            # 軟調・上昇
            real_datas[-1]['9:26'] = '{:.1f}'.format(float(form_dict['_8_38']) - 0.3)
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_8_38']) + 0.9)
            writer.writerow(real_datas[-1])
            # 軟調・下落
            real_datas[-1]['9:26'] = '{:.1f}'.format(float(form_dict['_8_38']) - 0.3)
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_8_38']) - 0.9)
            writer.writerow(real_datas[-1])
        else:
            # 上昇大
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_9_26']) + 1.6)
            writer.writerow(real_datas[-1])
            # 上昇中
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_9_26']) + 0.8)
            writer.writerow(real_datas[-1])
            # 上昇小
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_9_26']) + 0.4)
            writer.writerow(real_datas[-1])
            # 下落小
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_9_26']) - 0.4)
            writer.writerow(real_datas[-1])
            # 下落中
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_9_26']) - 0.8)
            writer.writerow(real_datas[-1])
            # 下落大
            real_datas[-1]['9:30'] = '{:.1f}'.format(float(form_dict['_9_26']) - 1.6)
            writer.writerow(real_datas[-1])
    # パターンの予測
    eval_df = pd.read_csv('saved_data/temp.csv')
    pred_type, _ = predicting(eval_df, 'type', predict_only=True)
    html_json['predicted_today_type'] = pred_type[0]
    html_json['predicted_by_pattern'] = pred_type[1:]
    # 高値の位置予測
    eval_df['type'] = pd.Series(pred_type)
    pred_hpos, _ = predicting(eval_df, 'High Position', predict_only=True)
    pos_to_time = list(zip([1,2,3,4],['9:30','10:00','13:30','16:00']))
    html_json['predicted_today_high_pos'] = pos_to_time[pred_hpos[-1] - 1][1]

    return html_json
