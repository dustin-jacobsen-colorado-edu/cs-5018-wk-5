import os
import json

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import statsd
from celery import Celery


def get_project_root() -> str:
    current_directory = os.path.dirname(os.path.abspath(__file__))
    while current_directory != os.path.abspath(os.path.sep):
        if '.project_root_marker' in os.listdir(current_directory):
            return current_directory
        current_directory = os.path.dirname(current_directory)
    return None  # If no marker file is found, return None or raise an exception


project_root = get_project_root()

with open(os.path.join(project_root, 'config.json'), 'r') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
app.app_context().push()
db_dir = os.path.join(project_root, 'database')
os.makedirs(db_dir, exist_ok=True)
db_file_path = os.path.join(db_dir, 'air-quality.sqlite3')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('JAWSDB_URL') or "sqlite:///" + os.path.abspath(db_file_path)
db = SQLAlchemy(app)


statsd_client = statsd.StatsClient(
        os.environ.get('STATSD_HOST') or 'localhost',
        os.environ.get('STATSD_PORT') or 8125,
        prefix=os.environ.get('HOSTEDGRAPHITE_APIKEY') or 'cs5028-capstone'
)

config['celery']['broker_url'] = os.environ.get('CLOUDAMQP_URL') or config['celery']['broker_url']

celery = Celery(
    app.import_name,
    broker=config['celery']['broker_url'],
    include=['src.time_series_analysis']
)
celery.conf.update(config['celery'])
