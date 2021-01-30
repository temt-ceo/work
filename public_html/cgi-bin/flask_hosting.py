import sys, traceback, json, csv
from flask import Flask, request, render_template, json
from werkzeug.exceptions import HTTPException
from datetime import date

server = Flask(__name__)

@server.route("/", methods=['GET', 'POST'])
def index(html_json=None):
    try:
        if request.method == 'GET':
            html_json = None
            today = date.today()

            with open('saved_data/saved_form_data.txt', 'r+', encoding="utf-8") as file:
                json_str = file.readlines()
                html_json = json.loads(json_str[0])
                if not 'date' in  html_json or html_json['date'] != today.strftime("%-m/%d"):
                    if html_json['y_date'] == today.strftime("%-m/%d") and date.hour < 21:
                        pass
                    else:
                        if 'date' in  html_json:
                            html_json['y_date'] = html_json['date']
                        else:
                            html_json['y_date'] = ''
                        html_json['date'] = today.strftime("%-m/%d")
                        html_json['y_930'] = html_json['t_930']
                        html_json['t_930'] = ''
                        html_json['t_838'] = ''
                        html_json['t_926'] = ''
                        html_json['y_1000'] = ''
                        html_json['y_1600'] = ''
                        html_json['y_lowest'] = ''
                        html_json['t_flag'] = '0'
                        file.truncate(0)
                        file.seek(0)
                        file.writelines(json.dumps(html_json))

            return render_template('index.html', html_json=html_json)
        elif request.method == 'POST':
            form_dict = request.form.to_dict()
            if form_dict['ticker'] != 'zm':
                with open('saved_data/saved_form_data.txt', 'r+', encoding="utf-8") as file:
                    json_str = file.readlines()
                    html_json = json.loads(json_str[0])
                return render_template('index.html', html_json=html_json)

            stats = []
            with open('saved_data/saved_form_data.txt', 'r+', encoding="utf-8") as file:
                json_str = file.readlines()
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
            "description": "Server Error",
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

