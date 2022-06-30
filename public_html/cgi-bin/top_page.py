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
        # POSTの場合はデータを一時保存
        with open('saved_data/saved_form_data.txt', 'r+', encoding="utf-8") as data_file:
            json_str = data_file.readlines()
            html_json = json.loads(json_str[0])
            html_json['date'] = today.isoformat()
            html_json['_QQQ3'] = form_dict['_QQQ3']
            html_json['_NQ_F'] = form_dict['_NQ_F']
            html_json['_8_30'] = form_dict['_8_30']
            html_json['_9_00'] = form_dict['_9_00']
            html_json['_9_00_sq'] = form_dict['_9_00_sq']
            html_json['momentum'] = form_dict['momentum']
            html_json['price'] = form_dict['price']
            data_file.truncate(0)
            data_file.seek(0)
            data_file.writelines(json.dumps(html_json))
    # 一時保存のフォーム入力情報を呼び出す
    with open('saved_data/saved_form_data.txt', 'r', encoding="utf-8") as txt_file:
        json_str = txt_file.readlines()
        html_json = json.loads(json_str[0])

    if from_page == 'create_csv':
        html_json['message'] = 'CSVデータの登録が完了しました。'
    if message is not None:
        html_json['message'] = message

    # 一時保存のフォーム入力情報が古い場合は初期化する
    if html_json['date'] != today.isoformat() and html_json['date'] != yesterday.isoformat():
        html_json['_QQQ3'] = ''
        html_json['_NQ_F'] = ''
        html_json['_8_30'] = ''
        html_json['_9_00'] = ''
        html_json['_9_00_sq'] = ''
        html_json['momentum'] = ''
        html_json['price'] = 0

    # CSV登録データを呼び出す
    real_datas = []
    with open('saved_data/real_data.csv', newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            real_datas.append(row)

    # CSV登録データの直近データ
    html_json['pre_16_00'] = real_datas[-1]['16:00']
    html_json['pre_vitality'] = real_datas[-1]['成行']
    html_json['target'] = real_datas[-1]['target']
    html_json['memo'] = real_datas[-1]['Memo']

    ################
    #  予測を行う   #
    ################
    eval_df = pd.read_csv('saved_data/real_data.csv')
    # パターンの予測
    pred_type, real_type = predicting(eval_df[-1:], 'type')
    # html_json['predicted_type'] = pred_type[-1]
    # html_json['real_type'] = real_type[-1]
    html_json['predicted_type'] = ''
    html_json['real_type'] = ''
    # # 高値の位置予測
    # eval_df['type'] = pd.Series([pred_type])
    # pred_hpos, real_hpos = predicting(eval_df[-1:], 'High Position')
    # pos_to_time = list(zip([1,2,3,4],['9:30','10:00','13:30','16:00']))
    # html_json['pre_high_pos'] = pos_to_time[pred_hpos[-1] - 1][1]
    # html_json['real_high_pos'] = pos_to_time[real_hpos[-1] - 1][1]

    # Formで入力した情報から今日の動きを予測する
    if form_dict is not None:
        html_json = predict_today_result(form_dict, html_json, real_datas)
        html_json['message'] = '今日の予測結果が表示されました。'
        html_json['message2'] = 'グラフ表示のリンクが有効化されました。'
    return render_template('index.html', html_json=html_json)

def data_cleaning(df):
    # カラム名変更
    for col in df.columns:
        if col == 'zm9:00':
            df['8:30->9:00'] = df[col].str.replace(r'\.\.', '.').astype(float) - df['8:30']
        elif col == 'QQQ3':
            df['QQQ3/3'] = round(df[col] / 3, 2)
        elif col == 'Nasdaq100Fut':
            df['NQ=F'] = df[col]
        elif col == 'sq9:00':
            df['sq(9:00)'] = df[col]
        elif col == '基準':
            df['basis'] = df[col].str.replace(r'^高い$', r'2')
            df['basis'] = df['basis'].str.replace(r'^高め$', r'1')
            df['basis'] = df['basis'].str.replace(r'^中立$', r'0')
            df['basis'] = df['basis'].str.replace(r'^安め$', r'-1')
            df['basis'] = df['basis'].str.replace(r'^安い$', r'-2')
            df['基準(5段階)'] = df['basis'].astype(int)
        elif col == '成行':
            df[col] = df[col].str.replace(r'^(→|↘|↗︎)(.*)', r'\2')
            new = df[col].str.split(pat="→|↘|↗︎", expand=True)
            df['成行QQQ3'] = new[0].str.replace(r'(.*)%$', r'\1').astype(float)
            df['成行NQ=F'] = new[1].str.replace(r'(.*)%$', r'\1').astype(float)
        elif col == '基準momemtum':
            split_data = df[col].str.split(pat="@", expand=True)
            df['Momentum'] = split_data[0].astype(int)
            if len(split_data) >= 2:
                df['PERTarget'] = split_data[1]
            else:
                df['PERTarget'] = 0.0
        elif col == 'PER100値':
            df['PER'] = df[col]
        elif col == 'type':
            df['Type'] = df[col].astype(int)
            df['LowType'] = df[col].astype(int)
            df['LowType'] = None
            df['HighType'] = df[col].astype(int)
            df['HighType'] = None
        elif col == 'target':
            df['Low'] = df[col].astype(float)
        elif col == 'Memo':
            df['High'] = df[col].str.split(pat="(", expand=True)[0].str.replace(r'(%|⇨)', '').astype(float)
    df = df[['8:30', '8:30->9:00', 'QQQ3/3', 'NQ=F', 'sq(9:00)', '16:00', '基準(5段階)', '成行QQQ3', '成行NQ=F', 'Momentum', 'PER', 'PERTarget', 'Type', 'Low', 'LowType', 'High', 'HighType']]


    # for col in df.columns:
    #     # 数値データの値タイプ変更
    #     if col == 'Alert Level':
    #         df[col] = df[col].apply(int)
    #     else:
    #         df[col] = df[col].apply(float)

def predicting(eval_df, target, predict_only=False):

    # CSVデータのクリーニング
    eval_df = eval_df[['type', 'QQQ3', 'Nasdaq100Fut', '8:30', 'sq9:00', 'zm9:00', '16:00', '成行', 'target', '基準', '基準momemtum', 'Memo', 'PER100値']]
    eval_df = eval_df.copy()
    data_cleaning(eval_df)

    # 全てのデータは-5~5の範囲にほぼあり、また、0以上と0未満は心理的に重要な意味を持つことからNormalizationは精度が下げる可能性がある為行わない。
    def normalize_x(X):
        # X_norm = (X - X.mean()) / X.std()
        X_norm = X
        return X_norm

    # eval_df['Compare 5Days'] = eval_df['5Days Volume'] - eval_df['5Days Volume Pre']
    # eval_df.drop('5Days Volume Pre', axis=1, inplace=True)
    # def apply_pre_market_pattern(df):
    #     # 堅調
    #     if df['PreMarket 926'] > df['PreMarket 838'] + 0.1:
    #         # 始値でもさらに上昇に転じる
    #         if df['Start'] > df['PreMarket 926']:
    #             return 1
    #         # 始値では下がる
    #         else:
    #             return 2
    #     # 軟調
    #     elif df['PreMarket 838'] > df['PreMarket 926'] + 0.1:
    #         # 始値では上昇に転じる
    #         if df['Start'] > df['PreMarket 926']:
    #             return 5
    #         # 始値でもさらに下がる
    #         else:
    #             return 6
    #     # 不定
    #     else:
    #         # 始値が上昇する
    #         if df['Start'] > df['PreMarket 926']:
    #             return 3
    #         # 始値が下落する
    #         else:
    #             return 4
    # eval_df['PreMarket Pattern'] = eval_df.apply(apply_pre_market_pattern, axis=1)
    # eval_df.drop('PreMarket 926', axis=1, inplace=True)

    # # one hot化
    # def preprocess(df):
    #     # Convert to Bins
    #     categorical = None
    #     if target == 'type':
    #         categorical = ['Alert Level', 'PreMarket Pattern']
    #     else:
    #         categorical = ['Alert Level', 'PreMarket Pattern', 'type']
        
    #     for column in categorical:
    #         if column == 'Alert Level':
    #             one_hot = pd.get_dummies(df[column], prefix=column[:5])
    #         else:
    #             one_hot = pd.get_dummies(df[column], prefix=column)
    #         df = df.drop(column, axis=1)
    #         df = pd.concat([df, one_hot], axis=1)
    #     return df
    # # 前処理
    # preprocessed_df = preprocess(eval_df)

    # # 予測に必要となるカラムのみ保持
    # X_test = preprocessed_df[['Pre End', 'Pre Vitality', '5Days Volume', 'PreMarket 838', 'Alert_0', 'Alert_1', 'Alert_2', 'Start', 'Compare 5Days', 'PreMarket Pattern_1', 'PreMarket Pattern_2', 'PreMarket Pattern_3', 'PreMarket Pattern_4', 'PreMarket Pattern_5', 'PreMarket Pattern_6']]

    # # Y値
    # if predict_only is False:
    #     y_test = preprocessed_df[[target]]
    #     y_test[target] = y_test[target].apply(int)
    #     real_type = pd.Series(y_test[target].values).array
    # else:
    #     real_type = None

    # # Modelを読み込む
    # model = None
    # if target == 'type':
    #     # with open('saved_data/model/stock_data_model_v2_type.pkl', 'rb') as file:
    #     with open('saved_data/model/stock_data_model_v102.pkl', 'rb') as file:
    #         model = pickle.load(file)
    # elif target == 'LowType':
    #     with open('saved_data/model/stock_data_model_v2_low.pkl', 'rb') as file:
    #         model = pickle.load(file)
    # elif target == 'HighType':
    #     with open('saved_data/model/stock_data_model_v2_high.pkl', 'rb') as file:
    #         model = pickle.load(file)
    # elif target == 'High Position':
    #     with open('saved_data/model/stock_data_model_rf_highpos.pkl', 'rb') as file:
    #         model = pickle.load(file)

    # # 予測
    # pred_type = model.predict(X_test)

    # return pred_type, real_type
    return 1, 0

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
    real_datas[-1]['8:30'] = form_dict['_8_30']
    real_datas[-1]['9:26'] = form_dict['_9_26']
    real_datas[-1]['flag'] = 0 # form_dict['flag']
    real_datas[-1]['活度'] = ''
    real_datas[-1]['max'] = ''
    real_datas[-1]['min'] = ''
    real_datas[-1]['down'] = ''
    real_datas[-1]['終値'] = ''
    real_datas[-1]['5日差'] = ''
    real_datas[-1]['type'] = ''
    # CSVにデータを登録する
    with open('saved_data/temp.csv', 'w', newline='', encoding="utf-8") as csvfile:
        csv_columns = ["date", "Y開", "Y終", "Y活", "Yx", "Yn", "B5", "Y5", "Px", "Pn", "dis", "B開", "B終", "8:30", "9:26", "flag", "9:30", "活度", "max", "min", "down", "終値", "5日差", "type"]
        writer = csv.DictWriter(csvfile, quoting=csv.QUOTE_ALL, fieldnames=csv_columns)
        writer.writeheader()
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
