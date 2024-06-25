# https://api-docs.luchtmeetnet.nl/
import time
# Example responses
#
# {"data": [{"value": 21.0, "timestamp_measured": "2024-06-25T16:00:00+00:00", "formula": "NO2"} ]}

from typing import Protocol
import requests
import logging
from datetime import datetime
from src.bootstrap import app, config, db, statsd_client


interval_minutes = config['data_retrieval']['interval_minutes']
INPUT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
LUCHTMEET_URL = "https://api.luchtmeetnet.nl/open_api"
STATION_ID= "NL49551"

class LuchtmeetRecord(db.Model):
    __tablename__ = 'luchtmeet_records'
    row_id = db.Column(db.Integer, primary_key=True)
    timestamp_measured = db.Column(db.DateTime)
    value = db.Column(db.Float)
    formula = db.Column(db.String(20))

# convert static functions to member functions of a new class


class ILuchtmeetApiClient(Protocol):
    def get_luchtmeet_data(self) -> [dict] | None:
        ...


class LuchtmeetApiClient(ILuchtmeetApiClient):
    def get_luchtmeet_data(self) -> [dict] | None:
        start = time.time()
        formula = 'NO2'
        url = f'{LUCHTMEET_URL}/stations/{STATION_ID}/measurements?page=&order=&order_direction=&formula={formula}'

        response = requests.get(url)
        millisecond_duration = int((time.time() - start) * 1000)
        statsd_client.timing("luchtmeet_api_request", millisecond_duration)
        if response.status_code in {200}:
            body = response.json()
            data = body['data']
            for record in data :
                record['timestamp_measured'] = datetime.strptime(record['timestamp_measured'], INPUT_DATE_FORMAT)
            return data

        else:
            print(f"Request failed with status code {response.status_code}")
            return None


class LuchtmeetCollector:
    def __init__(self, api_client: ILuchtmeetApiClient = None):
        if api_client is None:
            api_client = LuchtmeetApiClient()
        self.api_client = api_client

    def collect_and_store(self):
        with app.app_context():
            # Create the database table if it doesn't exist
            db.create_all()
            # Get air quality data
            luchtmeet_data = self.api_client.get_luchtmeet_data()
            for record in luchtmeet_data:
                # Create a new entry in the database
                new_entry = LuchtmeetRecord(timestamp_measured=record["timestamp_measured"],
                                                  value=record["value"],
                                                  formula=record["formula"])
                db.session.add(new_entry)
                db.session.commit()
                logging.info("Air quality data has been stored in the database.")


__instance = LuchtmeetCollector()


def collect_and_store():
    return __instance.collect_and_store()


if __name__ == "__main__":
    pass
