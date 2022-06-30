import sys, traceback, json, csv, shutil, pickle, array
import flask
from flask import Flask, request, render_template, json
from werkzeug.exceptions import HTTPException
from datetime import date, timedelta

def do_create_csv(form_dict):
    today = date.today()
    yesterday = today - timedelta(days=1)
    csv_columns = ["date", "Y開", "Y終", "Y活", "Yx", "Yn", "B5", "Y5", "Px", "Pn", "dis", "B開", "B終", "8:30", "9:26", "flag", "9:30", "活度", "max", "min", "down", "終値", "5日差", "type"]
    inputs_cols = ["type", "_8_30", "_9_26", "_9_30", "_10_00", "_13_30", "_16_00"]

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
    real_data['Yx'] = ''#real_datas[prev_row]['max']
    real_data['Yn'] = ''#real_datas[prev_row]['min']
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
    real_data['8:30'] = form_data['_8_30']
    real_data['9:26'] = form_data['_9_26']
    real_data['flag'] = form_dict['flag']
    real_data['9:30'] = form_data['_9_30']
    real_data['活度'] = ((int(form_data['_10_00'] * 10) * 2) - int(form_data['_9_30'] * 10)) / 10
    real_data['max'] = ''#form_data['max']
    real_data['min'] = ''#form_data['min']
    real_data['down'] = (int(lowest * 10) - int(form_data['_9_26'] * 10)) / 10
    real_data['終値'] = form_data['_16_00']
    real_data['5日差'] = '{:.1f}'.format((d1 + d2 + d3 + d4 + d5) / 10)
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
