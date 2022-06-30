import sys, traceback, json, csv, shutil, pickle, array
import flask
from flask import Flask, request, render_template, json
from werkzeug.exceptions import HTTPException
from datetime import date, timedelta
import pandas as pd


def show_stats(form_dict=None, html_json=None):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # 統計データ（過去データ表用）
    eval_df = pd.read_csv('saved_data/real_data.csv')
    pred_type, real_type = predicting(eval_df[-105:], 'type') # 4件目まではトレーニングされている
    html_json['predicted_type'] = pred_type
    html_json['real_type'] = real_type
    html_json['past_data_closed_at'] = ''

    # 5日移動平均線を求める為に2~4日のデータをcsvから取得する
    real_datas = []
    with open('saved_data/real_data.csv', newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            real_datas.append(row)

    # 今日の予測時の登録データを呼び出す
    temp = []
    with open('saved_data/temp.csv', newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            temp.append(row)

    # Formで入力した情報から明日以降の動きを予測する
    if form_dict is not None:
        html_json['form_submitted'] = True
        html_json['_10_00'] = form_dict['_10_00']
        temp[0]['date'] = tomorrow.isoformat()
        # 予測に使わない項目は空とする
        temp[0]['Y8:38'] = temp[0]['8:38']
        temp[0]['Y9:26'] = temp[0]['9:26']
        temp[0]['Y開'] = temp[0]['9:30']
        temp[0]['Y終'] = '' # 必須だが後で入力する
        temp[0]['Y活'] = '{:.1f}'.format(float(form_dict['_10_00']) * 2 - float(temp[0]['9:30']))
        temp[0]['Yx'] = ''
        temp[0]['Yn'] = ''
        temp[0]['B5'] = eval_df[-1:]['Y5'].values[0]
        temp[0]['Y5'] = '' # 必須だが後で入力する
        temp[0]['Px'] = '' # y値の１つだから使用しない
        temp[0]['Pn'] = ''
        temp[0]['dis'] = ''
        temp[0]['B開'] = ''
        temp[0]['B終'] = ''
        temp[0]['8:38'] = '' # 必須だが後で入力する
        temp[0]['9:26'] = '' # 必須だが後で入力する
        temp[0]['flag'] = 0 # temp[0]['flag'] # 今日と明日は同じ流動性と仮定する
        temp[0]['9:30'] = '' # 必須だが後で入力する
        temp[0]['活度'] = '' # y値の１つだから使用しない
        temp[0]['max'] = ''
        temp[0]['min'] = ''
        temp[0]['down'] = ''
        temp[0]['終値'] = ''
        temp[0]['5日差'] = ''
        temp[0]['type'] = ''
        
        d2 = float(real_datas[-5]['終値'])
        d3 = float(real_datas[-2]['終値'])
        d4 = float(real_datas[-3]['終値'])
        d5 = float(real_datas[-4]['終値'])
        # CSVにデータを登録する
        with open('saved_data/temp_future.csv', 'w', newline='', encoding="utf-8") as csvfile:
            csv_columns = ["date", "Y8:38", "Y9:26", "Y開", "Y終", "Y活", "Yx", "Yn", "B5", "Y5", "Px", "Pn", "dis", "B開", "B終", "8:38", "9:26", "flag", "9:30", "活度", "max", "min", "down", "終値", "5日差", "type"]
            writer = csv.DictWriter(csvfile, quoting=csv.QUOTE_ALL, fieldnames=csv_columns)
            writer.writeheader()
            for at_close in [2.5, 0.5, -0.5, -2.5]:
                for _8_38 in [0.7, 0.3, -0.3, -0.7]:

                    temp[0]['Y終'] = at_close
                    temp[0]['Y5'] = '{:.1f}'.format(at_close + d2 + d3 + d4 + d5)
                    temp[0]['8:38'] = _8_38

                    # 堅調・上昇
                    temp[0]['9:26'] = '{:.1f}'.format(_8_38 + 0.3)
                    temp[0]['9:30'] = '{:.1f}'.format(_8_38  + 0.9)
                    writer.writerow(temp[0])
                    # 堅調・下落
                    temp[0]['9:26'] = '{:.1f}'.format(_8_38  + 0.3)
                    temp[0]['9:30'] = '{:.1f}'.format(_8_38  - 0.9)
                    writer.writerow(temp[0])
                    # 不定・上昇
                    temp[0]['9:26'] = '{:.1f}'.format(_8_38)
                    temp[0]['9:30'] = '{:.1f}'.format(_8_38 + 0.9)
                    writer.writerow(temp[0])
                    # 不定・下落
                    temp[0]['9:26'] = '{:.1f}'.format(_8_38)
                    temp[0]['9:30'] = '{:.1f}'.format(_8_38 - 0.9)
                    writer.writerow(temp[0])
                    # 軟調・上昇
                    temp[0]['9:26'] = '{:.1f}'.format(_8_38 - 0.3)
                    temp[0]['9:30'] = '{:.1f}'.format(_8_38 + 0.9)
                    writer.writerow(temp[0])
                    # 軟調・下落
                    temp[0]['9:26'] = '{:.1f}'.format(_8_38 - 0.3)
                    temp[0]['9:30'] = '{:.1f}'.format(_8_38 - 0.9)
                    writer.writerow(temp[0])
        eval_df = pd.read_csv('saved_data/temp_future.csv')
        pred_type, _ = predicting(eval_df, 'type', predict_only=True)
        html_json['predicted_by_pattern'] = pred_type
        eval_df['type'] = pd.Series(pred_type)
        pred_hpos, _ = predicting(eval_df, 'High Position', predict_only=True)
        html_json['predicted_today_high_pos'] = pred_hpos
        html_json['message'] = '明日の予測結果が表示されました。'

        # すでに今日のパターンを予測済みなら
        if html_json['today_type'] != '':
            stats = []
            # 過去の実データを読み込む
            with open('saved_data/stats_{}.csv'.format(html_json['ticker']), newline='', encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, skipinitialspace=True)
                for row in reader:
                    row['_16_00'] = row['16:00']
                    stats.append(row)
            # 同じパターンの過去データから終値を取得
            for obj in reversed(stats):
                try:
                    if obj['type'] != '' and int(obj['type']) == int(html_json['today_type']):
                        _16_00 = float(obj['_16_00'])
                        if _16_00 >= 1.5:
                            html_json['past_data_closed_at'] = 'LargePlus'
                        elif _16_00 >= 0:
                            html_json['past_data_closed_at'] = 'SmallPlus'
                        elif _16_00 > -1.5:
                            html_json['past_data_closed_at'] = 'SmallMinus'
                        else:
                            html_json['past_data_closed_at'] = 'LargeMinus'
                except ValueError:
                    pass

    return render_template('stats.html', html_json=html_json)

def data_cleaning(df, _type=None):
    if _type is not None:
        df['type'] = _type
    
    # カラム名変更
    '''
      使用するカラムは(2021/02/09時点で)
      'Pre End',
      'Pre Vitality',
      '5Days Volume',
      'PreMarket 838',
      'Alert LEVEL',
      'Start',
      'Compare 5Days',
      'PreMarket Pattern',
      だけ。高値、安値は使わない。
    '''
    for col in df.columns:
        _col = col
        if _type is not None:
            _col = col[2:-1]
        elif _col == 'Y終':
            df.rename(columns={col: 'Pre End'}, inplace=True)
        elif _col == 'Y活':
            df.rename(columns={col: 'Pre Vitality'}, inplace=True)
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
        elif _col == '8:38':
            df.rename(columns={col: 'PreMarket 838'}, inplace=True)
        elif _col == '9:26':
            df.rename(columns={col: 'PreMarket 926'}, inplace=True)
        elif _col == 'flag_event' or _col == 'flag':
            df.rename(columns={col: 'Alert Level'}, inplace=True)
        elif _col == '9:30':
            df.rename(columns={col: 'Start'}, inplace=True)
    
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
