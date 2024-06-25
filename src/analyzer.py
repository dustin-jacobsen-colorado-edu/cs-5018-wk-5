from src.bootstrap import app, db, statsd_client, celery
from src.fetch_data import LuchtmeetRecord
import pandas as pd
import time


class LuchtmeetAnalyzer:
    def __init__(self, from_dt, to_dt, formula):
        self.from_dt = from_dt
        self.to_dt = to_dt
        self.formula = formula

    def load_data_from_db(self):
        with app.app_context():
            # Query the database to retrieve all rows

            results = db.session.query(LuchtmeetRecord.timestamp_measured,
                                       LuchtmeetRecord.value,
                                       LuchtmeetRecord.formula
                                       ) \
                .filter(LuchtmeetRecord.timestamp_measured.between(self.from_dt, self.to_dt),
                        LuchtmeetRecord.formula == self.formula
                        ) \
                .all()

            # Create a Pandas DataFrame from the query result
        df = pd.DataFrame([{
            'timestamp_measured': entry.timestamp_measured,
            'value': entry.value,
            'formula': entry.formula,
        } for entry in results])

        return df

    def preprocess_data(self, df):
        # Sort the DataFrame by timestamp_measured (optional)
        df = df.sort_values(by='timestamp_measured')

        # Fill NaN values with the last valid value (carry forward)
        df = df.ffill()

        df = df.drop_duplicates(subset=('timestamp_measured',
                                        'formula',
                                        'value'), keep='first')

        return df

    def calculate_statistics(self, df):
        # Calculate mean, median, variance, and standard deviation
        mean_values = df['value'].mean()
        median_values = df['value'].median()
        variance_values = df['value'].var()
        std_deviation_values = df['value'].std()

        return (mean_values,
                median_values,
                variance_values,
                std_deviation_values)

    def analyze(self) -> tuple:
        start = time.time()

        # Load data from the database
        data_df = self.load_data_from_db()

        if data_df is None or 0 == len(data_df):
            return None, None, None, None

        # Preprocess the data (carry forward NaN values)
        data_df = self.preprocess_data(data_df)

        result = self.calculate_statistics(data_df)
        millisecond_duration = int((time.time() - start) * 1000)
        statsd_client.timing("analyze", millisecond_duration)
        return result


@celery.task(retry_kwargs={'max_retries': 3})
def analyze(from_dt, to_dt,  formula):
    analyzer = LuchtmeetAnalyzer(from_dt, to_dt, formula)
    result = analyzer.analyze()
    output = from_dt, to_dt, result
    return output


if __name__ == "__main__":
    worker = celery.Worker()
    worker.start()
