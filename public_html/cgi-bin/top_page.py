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
    html_json['pre_type'] = real_datas[-1]['type']
    html_json['pre_nqf'] = real_datas[-1]['Nasdaq100Fut']
    html_json['pre_8_30'] = real_datas[-1]['8:30']
    html_json['pre_9_00_zm'] = real_datas[-1]['zm9:00']
    html_json['pre_9_00_sq'] = real_datas[-1]['sq9:00']
    html_json['pre_16_00'] = real_datas[-1]['16:00']
    html_json['pre_nari'] = real_datas[-1]['成行']
    html_json['pre_target'] = real_datas[-1]['target']
    html_json['pre_basis'] = real_datas[-1]['基準']
    html_json['pre_momentum'] = real_datas[-1]['基準momemtum']
    html_json['prepre_momentum'] = real_datas[-2]['基準momemtum']
    html_json['pre_memo'] = real_datas[-1]['Memo']
    html_json['pre_per'] = real_datas[-1]['PER100値']

    ################
    #  予測を行う   #
    ################
    # CSVに一時データを登録する
    with open('saved_data/temp.csv', 'w', newline='', encoding="utf-8") as csvfile:
        csv_columns = ["date","type","Nasdaq100Fut","8:30","sq9:00","zm9:00","16:00","成行","target","基準","基準momemtum","Memo","PER100値"]
        writer = csv.DictWriter(csvfile, quoting=csv.QUOTE_ALL, fieldnames=csv_columns)
        writer.writeheader()
        writer.writerows(real_datas[-25:])

    # パターンの予測
    eval_df = pd.read_csv('saved_data/temp.csv')

    # パターンの予測
    pred_type, real_type, _ = predicting(eval_df, 'Type')
    html_json['predicted_type'] = pred_type[-1]
    html_json['real_type'] = real_type[-1]

    low_range = ['nodata', -5.8, -4.4, -3.2, -2.2, -1.6, -0.8, 0.2, 1.0]
    high_range = ['nodata', -2.5, -1.2, -0.5, 0.1, 1.6, 3.3, 4.5, 5.6]

    last_day_price = 0
    last_day_split_data = html_json['prepre_momentum'].split('@')
    if len(last_day_split_data) >= 2:
        last_day_price = float(last_day_split_data[1])

    # 底値の予測
    pred_low, real_low, _ = predicting(eval_df, 'LowType')
    html_json['pre_low_pos'] = str(pred_low[-1]) + '【' + str(low_range[pred_low[-1]]) + '】'
    html_json['real_low_pos'] = str(real_low[-1]) + '【' + str(low_range[real_low[-1]]) + '】'
    if (low_range[pred_low[-1]] > 0):
        html_json['pre_low_pos_output'] = str(low_range[pred_low[-1]]) + '%(' + "{:.2f}".format(last_day_price * (1 + low_range[pred_low[-1]] / 100)) + ')'
    else:
        html_json['pre_low_pos_output'] = str(low_range[pred_low[-1]]) + '%(' + "{:.2f}".format(last_day_price / (1 + -1 * low_range[pred_low[-1]] / 100)) + ')'
    if (low_range[real_low[-1]] > 0):
        html_json['real_low_pos_output'] = str(low_range[real_low[-1]]) + '%(' + "{:.2f}".format(last_day_price * (1 + low_range[real_low[-1]] / 100)) + ')'
    else:
        html_json['real_low_pos_output'] = str(low_range[real_low[-1]]) + '%(' + "{:.2f}".format(last_day_price / (1 + -1 * low_range[real_low[-1]] / 100)) + ')'

    # 高値の予測
    pred_high, real_high, X_test = predicting(eval_df, 'HighType')
    html_json['pre_high_pos'] = str(pred_high[-1]) + '【' + str(high_range[pred_high[-1]]) + '】'
    html_json['real_high_pos'] = str(real_high[-1]) + '【' + str(high_range[real_high[-1]]) + '】'
    if (high_range[pred_high[-1]] > 0):
        html_json['pre_high_pos_output'] = str(high_range[pred_high[-1]]) + '%(' + "{:.2f}".format(last_day_price * (1 + high_range[pred_high[-1]] / 100)) + ')'
    else:
        html_json['pre_high_pos_output'] = str(high_range[pred_high[-1]]) + '%(' + "{:.2f}".format(last_day_price / (1 + -1 * high_range[pred_high[-1]] / 100)) + ')'
    if (high_range[real_high[-1]] > 0):
        html_json['real_high_pos_output'] = str(high_range[real_high[-1]]) + '%(' + "{:.2f}".format(last_day_price * (1 + high_range[real_high[-1]] / 100)) + ')'
    else:
        html_json['real_high_pos_output'] = str(high_range[real_high[-1]]) + '%(' + "{:.2f}".format(last_day_price / (1 + -1 * high_range[real_high[-1]] / 100)) + ')'

    # Formで入力した情報から今日の動きを予測する
    if form_dict is not None:
        html_json = predict_today_result(form_dict, html_json, real_datas)
        html_json['message'] = '今日の予測結果が表示されました。'
        html_json['message2'] = 'グラフ表示のリンクが有効化されました。'
    else:
        # Debug用
        html_json['model_input'] = X_test.iloc[0]
    html_json['pre_momentum'] = html_json['pre_momentum'] + ' 昨日: ' + str(last_day_price)
    return render_template('index.html', html_json=html_json)

def data_cleaning(df, predict_only):
    # カラム名変更
    for col in df.columns:
        if col == 'zm9:00':
            df[col] = df[col].astype(float)
            df['8:30->9:00'] = df[col] - df['8:30']
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
            df['成行QQQ3'] = new[0].str.replace(r'[^\x00-\x7F]+', '').astype(float)
            df['成行NQ=F'] = new[1].str.replace(r'[^\x00-\x7F]+', '').astype(float)
        elif col == '基準momemtum':
            split_data = df[col].str.split(pat="@", expand=True)
            df['Momentum'] = split_data[0].astype(float)
            if len(split_data) >= 2:
                df['PERTarget'] = split_data[1]
            else:
                df['PERTarget'] = 0.0
        elif col == 'PER100値':
            df['PER'] = df[col]
        elif col == 'type' and predict_only is False:
            df['Type'] = df[col].astype(int)
            df['LowType'] = df[col].astype(int)
            df['LowType'] = None
            df['HighType'] = df[col].astype(int)
            df['HighType'] = None
        elif col == 'target':
            df['Low'] = df[col].astype(float)
        elif col == 'Memo':
            df['High'] = df[col].str.split(pat="(", expand=True)[0].str.replace(r'(%|⇨)', '').astype(float)

    if  predict_only is False:
        df = df[['8:30', '8:30->9:00', 'NQ=F', 'sq(9:00)', '16:00', '基準(5段階)', '成行QQQ3', '成行NQ=F', 'Momentum', 'PER', 'PERTarget', 'Type', 'Low', 'LowType', 'High', 'HighType']]
    else:
        df = df[['8:30', '8:30->9:00', 'NQ=F', 'sq(9:00)', '16:00', '基準(5段階)', '成行QQQ3', '成行NQ=F', 'Momentum', 'PER', 'PERTarget']]

    # for col in df.columns:
    #     # 数値データの値タイプ変更
    #     if col == 'Alert Level':
    #         df[col] = df[col].apply(int)
    #     else:
    #         df[col] = df[col].apply(float)
    return df


def predicting(eval_df, target, predict_only=False):

    # CSVデータのクリーニング
    eval_df = eval_df[['type', 'Nasdaq100Fut', '8:30', 'sq9:00', 'zm9:00', '16:00', '成行', 'target', '基準', '基準momemtum', 'Memo', 'PER100値']]
    eval_df = eval_df.copy()
    eval_df = data_cleaning(eval_df, predict_only)

    # 全てのデータは-5~5の範囲にほぼあり、また、0以上と0未満は心理的に重要な意味を持つことからNormalizationは精度が下げる可能性がある為行わない。
    def normalize_x(X):
        # X_norm = (X - X.mean()) / X.std()
        X_norm = X
        return X_norm

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

    # 前処理
    def preprocess(df, predict_only):
        #
        #
        # 必要なInputを全て用意する
        #
        #
        T1_ago_16 = 0
        T1_ago_nariQ = 0
        T1_ago_nariF= 0
        T1_ago_momentum = 0
        T2_ago_16 = 0
        T3_ago_sum_16 = 0
        T3_ago_sum_M = 0
        T5_ago_sum_16 = 0
        T5_ago_sum_N = 0

        sum5_16 = None
        sum4_16 = 0
        sum3_16 = 0
        sum2_16 = 0
        sum1_16 = 0
        sum3_M = None
        sum2_M = 0
        sum1_M = 0
        sum5_N = None
        sum4_N = 0
        sum3_N = 0
        sum2_N = 0
        sum1_N = 0
        for i, row in df.iterrows():
            sum5_16 = sum4_16 + row['16:00']
            sum4_16 = sum3_16 + row['16:00']
            sum3_16 = sum2_16 + row['16:00']
            sum2_16 = sum1_16 + row['16:00']
            sum1_16 = row['16:00']
            if pd.isna(row['成行QQQ3']) is False:
                sum5_N = sum4_N + (row['成行QQQ3'] + row['成行NQ=F']) / 2
                sum4_N = sum3_N + (row['成行QQQ3'] + row['成行NQ=F']) / 2
                sum3_N = sum2_N + (row['成行QQQ3'] + row['成行NQ=F']) / 2
                sum2_N = sum1_N + (row['成行QQQ3'] + row['成行NQ=F']) / 2
                sum1_N = (row['成行QQQ3'] + row['成行NQ=F']) / 2

            sum3_M = sum2_M + row['Momentum']
            sum2_M = sum1_M + row['Momentum']
            sum1_M = row['Momentum']
            df.at[i, '昨日の終値'] = T1_ago_16 # Input(昨日の終値)
            df.at[i, '昨日の成行QQQ3'] = T1_ago_nariQ # Input(昨日の成行QQQ3)
            df.at[i, '昨日の成行NQ=F'] = T1_ago_nariF # Input(昨日の成行NQ=F)
            df.at[i, '昨日のMomentum'] = T1_ago_momentum # Input(昨日のMomentum)
            df.at[i, '一昨日の終値'] = T2_ago_16 # Input(一昨日の終値)
            df.at[i, '終値３日変化量'] = round(T3_ago_sum_16 / 3, 2) # Input(終値３日変化量)
            df.at[i, 'Momentum3日変化量'] = round(T3_ago_sum_M / 3, 2) # Input(Momentum3日変化量)
            df.at[i, '終値5日変化量'] = round(T5_ago_sum_16 / 5, 2) # Input(終値5日変化量)
            if T5_ago_sum_N is not None:
                df.at[i, '成行５日変化量'] = round(T5_ago_sum_N / 5, 2) # Input(成行5日変化量)
            else:
                df.at[i, '成行５日変化量'] = 0 # Input(成行5日変化量)
            df.at[i, 'PER計算'] = float(row['PERTarget']) / float(row['PER']) # Input(PER20日変化率)

            if predict_only is False:
                # 予測結果をクラス化する
                if df.at[i, 'Low'] <= -5.6:
                    df.at[i, 'LowType'] = 1
                elif df.at[i, 'Low'] <= -4.2:
                    df.at[i, 'LowType'] = 2
                elif df.at[i, 'Low'] <= -3.0:
                    df.at[i, 'LowType'] = 3
                elif df.at[i, 'Low'] <= -2.0:
                    df.at[i, 'LowType'] = 4
                elif df.at[i, 'Low'] <= -1.4:
                    df.at[i, 'LowType'] = 5
                elif df.at[i, 'Low'] <= -0.6:
                    df.at[i, 'LowType'] = 6
                elif df.at[i, 'Low'] <= 0.4:
                    df.at[i, 'LowType'] = 7
                else:
                    df.at[i, 'LowType'] = 8

                if df.at[i, 'High'] < -1.4:
                    df.at[i, 'HighType'] = 1
                elif df.at[i, 'High'] < -0.7:
                    df.at[i, 'HighType'] = 2
                elif df.at[i, 'High'] < -0.1:
                    df.at[i, 'HighType'] = 3
                elif df.at[i, 'High'] < 1.4:
                    df.at[i, 'HighType'] = 4
                elif df.at[i, 'High'] < 3.1:
                    df.at[i, 'HighType'] = 5
                elif df.at[i, 'High'] < 4.3:
                    df.at[i, 'HighType'] = 6
                elif df.at[i, 'High'] < 5.4:
                    df.at[i, 'HighType'] = 7
                else:
                    df.at[i, 'HighType'] = 8

            T5_ago_sum_16 = sum5_16
            T5_ago_sum_N = sum5_N
            T3_ago_sum_16 = sum3_16
            T3_ago_sum_M = sum3_M
            T2_ago_16 = T1_ago_16
            T1_ago_16 = row['16:00']
            T1_ago_nariQ = row['成行QQQ3']
            T1_ago_nariF= row['成行NQ=F']
            T1_ago_momentum = row['Momentum']

        for i, row in df.iterrows():
            if i > 20:
                df.at[i, 'PER20日変化率'] = df.at[i - 1, 'PER計算'] / df.at[i - 21, 'PER計算'] # Input(PER計算)
            else:
                df.at[i, 'PER20日変化率'] = 0.0

        # 必要な項目 + 予測結果のみ
        if predict_only is False:
            all_df = df[['8:30', '8:30->9:00', 'NQ=F', 'sq(9:00)', '昨日の終値', '基準(5段階)', '昨日の成行QQQ3', '昨日の成行NQ=F', 'Momentum', '昨日のMomentum', '一昨日の終値', '終値３日変化量', 'Momentum3日変化量', '終値5日変化量', '成行５日変化量', 'PER20日変化率', 'Type', 'Low', 'LowType', 'High', 'HighType']]
        else:
            all_df = df[['8:30', '8:30->9:00', 'NQ=F', 'sq(9:00)', '昨日の終値', '基準(5段階)', '昨日の成行QQQ3', '昨日の成行NQ=F', 'Momentum', '昨日のMomentum', '一昨日の終値', '終値３日変化量', 'Momentum3日変化量', '終値5日変化量', '成行５日変化量', 'PER20日変化率']]
        return all_df

    preprocessed_df = preprocess(eval_df, predict_only)

    # 予測に必要となるカラムのみ保持
    X_test = []

    # Y値
    if predict_only is False:
        y_test = preprocessed_df[[target]]
        y_test[target] = y_test[target].apply(int)
        real_type = pd.Series(y_test[target].values).array
    else:
        real_type = None

    # Modelを読み込む
    model = None
    if target == 'Type':
        # 予測に必要となるカラムのみ保持
        X_test = preprocessed_df[-1:][['8:30', '8:30->9:00', 'NQ=F', 'sq(9:00)', '昨日の終値', '基準(5段階)', '昨日の成行QQQ3', '昨日の成行NQ=F', 'Momentum', '一昨日の終値', '終値３日変化量', 'Momentum3日変化量', '終値5日変化量', '成行５日変化量', 'PER20日変化率']]
        with open('saved_data/model/stock_data_model_v201_type.pkl', 'rb') as file:
            model = pickle.load(file)
    elif target == 'LowType':
        # 予測に必要となるカラムのみ保持
        X_test = preprocessed_df[-1:][['8:30', '8:30->9:00', 'NQ=F', 'sq(9:00)', '昨日の終値', '基準(5段階)', '昨日の成行QQQ3', '昨日の成行NQ=F', 'Momentum', '一昨日の終値', '終値３日変化量', 'Momentum3日変化量', '終値5日変化量', '成行５日変化量', 'PER20日変化率']]
        with open('saved_data/model/stock_data_model_v208_low.pkl', 'rb') as file:
            model = pickle.load(file)
    elif target == 'HighType':
        # 予測に必要となるカラムのみ保持
        X_test = preprocessed_df[-1:][['8:30', '8:30->9:00', 'NQ=F', 'sq(9:00)', '昨日の終値', '基準(5段階)', '昨日の成行QQQ3', '昨日の成行NQ=F', 'Momentum', '一昨日の終値', '終値３日変化量', 'Momentum3日変化量', '終値5日変化量', '成行５日変化量', 'PER20日変化率']]
        with open('saved_data/model/stock_data_model_v203_high.pkl', 'rb') as file:
            model = pickle.load(file)

    # 予測
    pred_type = model.predict(X_test)

    return pred_type, real_type, X_test

def predict_today_result(form_dict, html_json, real_datas):
    today = date.today()
    yesterday = today - timedelta(days=1)
    html_json['form_submitted'] = True
    real_datas.append({
        "date": today.isoformat(),
        "type": "",
        "Nasdaq100Fut": form_dict['_NQ_F'],
        "8:30": form_dict['_8_30'],
        "sq9:00": form_dict['_9_00_sq'],
        "zm9:00": form_dict['_9_00'],
        "16:00": "",
        "成行": "",
        "target": "",
        "基準": form_dict['price'],
        "基準momemtum": str(form_dict['momentum']) + '@999999',
        "Memo": "",
        "PER100値": ""
    })
    # CSVにデータを登録する
    with open('saved_data/temp.csv', 'w', newline='', encoding="utf-8") as csvfile:
        csv_columns = ["date","type","Nasdaq100Fut","8:30","sq9:00","zm9:00","16:00","成行","target","基準","基準momemtum","Memo","PER100値"]
        writer = csv.DictWriter(csvfile, quoting=csv.QUOTE_ALL, fieldnames=csv_columns)
        writer.writeheader()
        writer.writerows(real_datas[-25:])

    # パターンの予測
    eval_df = pd.read_csv('saved_data/temp.csv')
    pred_type, _, X_test = predicting(eval_df, 'Type', predict_only=True)
    html_json['today_date'] = today.isoformat()
    html_json['predicted_today_type'] = pred_type[0]
    html_json['predicted_by_pattern'] = pred_type[1:]

    # 底値/高値の位置予測
    low_range = ['nodata', -5.8, -4.4, -3.2, -2.2, -1.6, -0.8, 0.2, 1.0]
    high_range = ['nodata', -2.5, -1.2, -0.5, 0.1, 1.6, 3.3, 4.5, 5.6]

    pred_low, _, _ = predicting(eval_df, 'LowType', predict_only=True)
    html_json['predicted_today_low_pos'] = str(pred_low[-1]) + '【' + str(low_range[pred_low[-1]]) + '】'
    html_json['predicted_today_low_value'] = low_range[pred_low[-1]]
    if html_json['predicted_today_low_value'] > 0:
        html_json['predicted_today_low_value'] = '+' + str(html_json['predicted_today_low_value'])

    pred_high, _, _ = predicting(eval_df, 'HighType', predict_only=True)
    html_json['predicted_today_high_pos'] = str(pred_high[-1]) + '【' + str(high_range[pred_high[-1]]) + '】'
    html_json['predicted_today_high_value'] = high_range[pred_high[-1]]
    if html_json['predicted_today_high_value'] > 0:
        html_json['predicted_today_high_value'] = '+' + str(html_json['predicted_today_high_value'])

    split_data = html_json['pre_momentum'].split("@")
    if len(split_data) >= 2:
        html_json['previous_stock_value'] = split_data[1]
        html_json['target_stock_value_low'] = "{:.2f}".format(float(split_data[1]) * (1 + float(low_range[pred_low[-1]]) / 100))
        html_json['target_stock_value_high'] = "{:.2f}".format(float(split_data[1]) * (1 + float(high_range[pred_high[-1]]) / 100))
    html_json['yesterday_date'] = yesterday.isoformat()
    html_json['model_input2'] = X_test.iloc[0]
    html_json['model_input'] = '8:30;' + "{:.1f}".format(X_test.at[24, '8:30']) + ';' + '8:30->9:00;' + "{:.1f}".format(X_test.at[24, '8:30->9:00']) + ';'
    html_json['model_input'] = html_json['model_input'] + 'NQ=F;' + "{:.1f}".format(X_test.at[24, 'NQ=F']) + ';'
    html_json['model_input'] = html_json['model_input'] + 'sq(9:00);' + "{:.1f}".format(X_test.at[24, 'sq(9:00)']) + ';' + 'Yesterday_Close;' + "{:.1f}".format(X_test.at[24, '昨日の終値']) + ';'
    html_json['model_input2'] = 'Yesterday_Criteria;' + "{:.1f}".format(X_test.at[24, '基準(5段階)']) + ';' + 'QQQ3_market_from_before_trading_hours;' + "{:.1f}".format(X_test.at[24, '昨日の成行QQQ3']) + ';'
    html_json['model_input2'] = html_json['model_input2'] + 'NQ=F_market_from_before_trading_hours;' + "{:.1f}".format(X_test.at[24, '昨日の成行NQ=F']) + ';' + 'Recent_Momentum;' + "{:.1f}".format(X_test.at[24, 'Momentum']) + ';'
    html_json['model_input3'] = 'Close_day_before_yesterday;' + "{:.1f}".format(X_test.at[24, '一昨日の終値']) + ';' + 'Close_3_day_change;' + "{:.1f}".format(X_test.at[24, '終値３日変化量']) + ';'
    html_json['model_input3'] = html_json['model_input3'] + 'Momentum_3_day_change;' + "{:.1f}".format(X_test.at[24, 'Momentum3日変化量']) + ';' + 'Close_5_day_change;' + "{:.1f}".format(X_test.at[24, '終値5日変化量']) + ';'
    html_json['model_input3'] = html_json['model_input3'] + 'Market_5_day_change;' + "{:.1f}".format(X_test.at[24, '成行５日変化量']) + ';' + 'PER_20_day_change;' + "{:.5f}".format(X_test.at[24, 'PER20日変化率'])
    return html_json
