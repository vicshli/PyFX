import logging
import numpy as np
from datetime import datetime, timedelta, time

from dataio.datareader import DataReader
from datastructure.pricetime import PriceTime
from datastructure.daytimerange import TimeRangeInDay
from datastructure.daterange import DateRange

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Metric:
    def __init__(self, time_range: TimeRangeInDay, date_range: DateRange, price_dfs, currency_pair_name: str):
        self.time_range = time_range
        self.date_range = date_range
        self.currency_pair_name = currency_pair_name
        self.fix_price_df = price_dfs[DataReader.FIX]
        self.daily_price_df = price_dfs[DataReader.DAILY]
        self.minute_price_df = self._filter_df_to_time_range(
            price_dfs[DataReader.MINUTELY])
        self.full_minute_price_df = price_dfs[DataReader.MINUTELY]

    def _filter_df_to_time_range(self, df):
        return df.between_time(self.time_range.start_time, self.time_range.end_time)

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
