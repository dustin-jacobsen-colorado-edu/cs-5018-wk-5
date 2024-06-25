import os

import pandas as pd

from src.bootstrap import app, statsd_client
from flask import render_template, request, send_from_directory, jsonify
from datetime import datetime
from src.analyzer import analyze


@app.route('/')
def index():
    statsd_client.incr('index_page_visits')
    return render_template('index.html')


@app.route('/assets/<path:path>')
def assets(path):
    return send_from_directory('assets', path)


@app.route('/report', methods=['POST'])
def create_report():
    statsd_client.incr('summary_page_visits')
    formula = request.form['formula']
    from_dt_str = request.form['from_dt']
    to_dt_str = request.form['to_dt']

    # Convert the form input strings to datetime objects
    from_dt = datetime.strptime(from_dt_str, '%Y-%m-%dT%H:%M')
    to_dt = datetime.strptime(to_dt_str, '%Y-%m-%dT%H:%M')

    task = analyze.apply_async(args=[from_dt, to_dt, formula])
    return jsonify({
        "report": {
            "attr": {
                "id": task.id,
                "from_dt": from_dt,
                "to_dt": to_dt,
                "formula": formula,
                "state": "PENDING"
            },
            "rel": {
                "self": "/report/{}".format(task.id)
            }
        }
    }), 200


@app.route('/report/<report_id>')
def get_results(report_id):
    task = analyze.AsyncResult(report_id)
    return render_report_asynchronously(task, report_id)


def render_report_asynchronously(task, report_id):
    if task.state != 'SUCCESS':
        return jsonify({
            "report": {
                "attr": {
                    "id": task.id,
                    "state": task.state
                },
                "rel": {
                    "self": "/report/{}".format(task.id)
                }
            }
        }), 200
    from_dt, to_dt, formula, results = task.get()
    mean_values, median_values, variance_values, std_deviation_values = results
    return jsonify({
        "report": {
            "attr": {
                "id": task.id,
                "from_dt": from_dt,
                "to_dt": to_dt,
                "formula": formula,
                "state": "SUCCESS",
                "mean_values": 'NaN' if pd.isna(mean_values) else mean_values,
                "median_values": 'NaN' if pd.isna(median_values) else median_values,
                "variance_values": 'NaN' if pd.isna(variance_values) else variance_values,
                "std_deviation_values": 'NaN' if pd.isna(std_deviation_values) else std_deviation_values
            },
            "rel": {
                "self": "/report/{}".format(task.id)
            }
        }
    }), 200


if __name__ == '__main__':
    print('running app')
    app.run(debug=True, port=os.environ.get('PORT') or 5000, host=os.environ.get('HOST') or '0.0.0.0')
    print('exiting app')
