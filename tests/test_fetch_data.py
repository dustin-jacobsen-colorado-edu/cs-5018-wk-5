from unittest import TestCase

from datetime import datetime
from src.fetch_data import LuchtmeetCollector, INPUT_DATE_FORMAT, LuchtmeetRecord, \
    ILuchtmeetApiClient, LuchtmeetApiClient


class TestLuchtmeetCollector(TestCase):
    def setUp(self):
        from src.bootstrap import app, db
        app.app_context().push()
        db.create_all()

    class StubApiClient(ILuchtmeetApiClient):
        def __init__(self, data: list[dict] | None):
            self.data = data

        def get_air_quality_data(self) -> list[dict] | None:
            return self.data

    def test_collect_and_store_fake_data(self):
        fake_air_quality_data = [{
            "timestamp_measured": datetime.strptime("2024-06-25T19:00:00+00:00", INPUT_DATE_FORMAT),
            "value": 26,
            "formula": "NO2"
        }]
        air_quality_collector = LuchtmeetCollector(self.StubApiClient(fake_air_quality_data))
        air_quality_collector.collect_and_store()
        LuchtmeetRecord.query.filter(
            LuchtmeetRecord.timestamp_measured == datetime.strptime("2024-06-25T19:00:00+00:00", INPUT_DATE_FORMAT)
        ).first()

    def test_collect_and_store_no_data(self):
        air_quality_collector = LuchtmeetCollector(self.StubApiClient(None))
        air_quality_collector.collect_and_store()

    # verify that collect and store works with the real API client
    def test_collect_integrated(self):
        prev_count = LuchtmeetRecord.query.count()
        air_quality_collector = LuchtmeetCollector(LuchtmeetApiClient())
        air_quality_collector.collect_and_store()
        new_count = LuchtmeetRecord.query.count()
        self.assertEqual(prev_count + 1, new_count)
