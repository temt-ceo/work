import sys, traceback, json, csv, shutil, pickle, array
import flask
from flask import Flask, request, render_template, json
from werkzeug.exceptions import HTTPException
from datetime import date, timedelta

def do_create_csv(form_dict):
    today = date.today()
    yesterday = today - timedelta(days=1)
    csv_columns = ["date","type","Nasdaq100Fut","8:30","sq9:00","zm9:00","16:00","成行","target","基準","基準momemtum","Memo","PER100値"]
    inputs_cols = ["date","type", "_NQ_F", "_8_30", "_9_00_zm", "_9_00_sq", "_16_00", "target_low", "target_high", "current", "basis", "per100"]

    real_datas = []
    # CSV登録データを呼び出す
    with open('saved_data/real_data.csv', newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            real_datas.append(row)

    # Validationチェック
    html_json = {}
    html_json['message'] = ''
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
                html_json[key] = float(value)
    except ValueError:
        html_json['message'] = '{}: 少数点第一位までの数値で入力してください。'.format(outputs)
    # 入力不備あり
    if html_json['message'] != '':
        return render_template('create_csv.html', html_json=html_json)

    register_data = {}
    # CSV登録データから前日のデータを取得、新規行の入力データに活用する
    register_data['date'] = yesterday.isoformat()
    register_data['type'] = int(form_dict['type'])
    register_data['Nasdaq100Fut'] = float(form_dict['_NQ_F'])
    register_data['8:30'] = float(form_dict['_8_30'])
    register_data['sq9:00'] = float(form_dict['_9_00_sq'])
    register_data['zm9:00'] = float(form_dict['_9_00_zm'])
    register_data['16:00'] = float(form_dict['_16_00'])
    register_data['成行'] = form_dict['nari']
    register_data['target'] = float(form_dict['target_low'])
    register_data['基準'] = form_dict['price']
    register_data['基準momemtum'] = form_dict['basis'] + "@" + form_dict['current']
    register_data['Memo'] = "⇨" + form_dict['target_high'] + "(" + form_dict['bottom_time'] + "に" + form_dict['target_low'] + '%)'
    register_data['PER100値'] = form_dict['per100']
    # バックアップする
    shutil.copyfile('saved_data/real_data.csv', 'saved_data/real_data_backup.csv')
    # CSVにデータを登録する
    with open('saved_data/real_data.csv', 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, quoting=csv.QUOTE_ALL, fieldnames=csv_columns)
        writer.writeheader()
        for row in real_datas:
            if row['date'] != yesterday.isoformat():
                writer.writerow(row)
        writer.writerow(register_data)
    # TOP画面にリダイレクトする
    return flask.redirect("/?from_page=create_csv")
