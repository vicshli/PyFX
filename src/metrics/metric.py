import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, time

from dataio.configreader import ConfigReader
from dataio.datareader import DataReader
from datastructure.pricetime import PriceTime
from datastructure.daytimerange import DayTimeRange
from datastructure.daterange import DateRange

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Metric:

    def __init__(self, price_dfs, currency_pair_name: str, config: ConfigReader):

        self.time_range = config.time_range
        self.date_range = config.date_range
        self.currency_pair_name = currency_pair_name

        self.fix_price_df = price_dfs[DataReader.FIX]
        self.daily_price_df = price_dfs[DataReader.DAILY]
        self.full_minute_price_df = price_dfs[DataReader.MINUTELY]
        self.minute_price_df = self._filter_df_to_time_range(df=self.full_minute_price_df,
                                                             config=config)
        print(self.minute_price_df)

    def _filter_df_to_time_range(self, df: pd.DataFrame, config: ConfigReader) -> pd.DataFrame:

        if config.should_enable_daylight_saving_mode:

            df_list = []

            '''Dates before the DST gap where there's 1 hr ahead: normal start & end time'''
            before_hr_ahead_mask = df['date'] < self._to_datetime(
                config.dst_hour_ahead_period.start_date)

            before_hr_ahead_df = df.loc[before_hr_ahead_mask].between_time(config.time_range.start_time,
                                                                           config.time_range.end_time)
            df_list.append(before_hr_ahead_df)

            '''Dates during the DST gap where there's 1 hr ahead: start & end time advance by 1hr'''
            hr_ahead_mask = ((df['date'] >= self._to_datetime(config.dst_hour_ahead_period.start_date)) &
                             (df['date'] <= self._to_datetime(config.dst_hour_ahead_period.end_date)))

            hr_ahead_df = df.loc[hr_ahead_mask].between_time(config.dst_hour_ahead_time_range.start_time,
                                                             config.dst_hour_ahead_time_range.end_time)
            df_list.append(hr_ahead_df)

            '''Dates b/t the 1-hr-ahead and 1-hr-lag DST gap: normal start & end time'''
            between_hr_ahead_and_before_mask = ((df['date'] > self._to_datetime(config.dst_hour_ahead_period.end_date)) &
                                                (df['date'] < self._to_datetime(config.dst_hour_behind_period.start_date)))

            between_hr_ahead_and_before_df = df.loc[between_hr_ahead_and_before_mask].between_time(config.time_range.start_time,
                                                                                                   config.time_range.end_time)
            df_list.append(between_hr_ahead_and_before_df)

            '''Dates during the DST gap where there's 1 hr lag: start & end time delay by 1hr'''
            hr_behind_mask = ((df['date'] >= self._to_datetime(config.dst_hour_behind_period.start_date)) &
                              (df['date'] <= self._to_datetime(config.dst_hour_behind_period.end_date)))

            hr_behind_df = df.loc[hr_behind_mask].between_time(config.dst_hour_behind_time_range.start_time,
                                                               config.dst_hour_behind_time_range.end_time)
            df_list.append(hr_behind_df)

            '''Dates after the DST gap where there's 1 hr lag: normal start & end time'''
            after_hr_behind_mask = df['date'] > self._to_datetime(
                config.dst_hour_behind_period.end_date)

            after_hr_behind_df = df.loc[after_hr_behind_mask].between_time(config.time_range.start_time,
                                                                           config.time_range.end_time)
            df_list.append(after_hr_behind_df)

            '''Concatonate data and return'''
            target = pd.concat(df_list)
            return target

        else:
            return df.between_time(config.time_range.start_time, config.time_range.end_time)

    def _get_prior_fix_recursive(self, d):

        def daydelta(d, delta): return d - timedelta(days=delta)

        fx = None

        if self.date_range.is_datetime_in_range(d):

            try:
                cp_identifier = self.currency_pair_name[:3] + \
                    '-' + self.currency_pair_name[3:]
                fx = self.fix_price_df.loc[str(d)][cp_identifier]
            except Exception as e:
                logger.error(
                    "Could not locate the previous fix price, possibly due to out of bounds." + str(e))
                return None
            if not np.isnan(fx):
                index = datetime(year=d.year, month=d.month,
                                 day=d.day, hour=0, minute=0, second=0)
                return PriceTime(price=fx, datetime=index)
            else:
                return self._get_prior_fix_recursive(daydelta(d, 1))

        else:
            return None

    @staticmethod
    def incr_one_min(time_cur):
        old_min = time_cur.minute
        if old_min == 59:
            new_min = 0
            new_hour = time_cur.hour + 1
        else:
            new_min = old_min + 1
            new_hour = time_cur.hour
        time_cur = time(hour=new_hour, minute=new_min, second=time_cur.second)
        return time_cur

    @staticmethod
    def _to_datetime(date: datetime.date) -> datetime:
        return datetime.combine(date, datetime.min.time())
