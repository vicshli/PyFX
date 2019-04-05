from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
from os.path import abspath


from datastructure.daytimerange import TimeRangeInDay
from datastructure.pricetime import PriceTime

from dataio.datawriter import DataWriter
from dataio.datareader import DataReader

from metric.metric import Metric
from metric.daymvmt import DayPipMovmentToPrice
from metric.periodpriceavg import PeriodPriceAvg


class MaxPriceMovements(Metric):
    """This class finds the daily price movements within a period of time. 
    It is used in conjunction with DayPipMovmentToPrice class.
    """

    TIME_RANGE = "time range"
    BENCHMARK_TIMES = "benchmark_times"

    def __init__(self, price_dfs, config):
        '''
        Note: the initialization is highly coupled. Later initializations may 
        depend on earlier initializations. Change the sequence of initialization
        with caution. 
        '''
        '''
        TODO: Data structure choice for max_price_movements is subject to change.
        Consider multilevel dataframe (possible difficulty in excel exporting). 

        Current implementation: 
        "benchmark_time": {
            "date": {
                pip_info
            }
        }
        '''
        Metric.__init__(self, time_range=config[self.TIME_RANGE], price_dfs=price_dfs)

        self.benchmark_times = config[self.BENCHMARK_TIMES]
        self.max_price_movements = \
            self._generate_price_movements_obj_from_benchmark_times()

        self.benchmark_prices_matrix = self._generate_benchmark_prices_matrix()



    def _generate_price_movements_obj_from_benchmark_times(self):
        ret = {}
        for btime in self.benchmark_times:
            ret[btime] = {}
        return ret
    

    def _filter_df_to_time_range(self, df):
        return df.between_time(self.time_range.start_time, self.time_range.end_time)
    

    def _generate_benchmark_prices_matrix(self):
        ret = {}
        for btime in self.benchmark_times:
            ret[btime] = self.minute_price_df.between_time(btime, btime)
        return ret


    def find_max_price_movements(self):
        """
        Algorithm: 
        For each day, perform max day price movement check. 
        """
        for btime in self.max_price_movements:
            self.max_price_movements[btime] = \
                self._find_max_price_movement_against_benchmark(benchmark_time=btime)
        self.max_price_movements["PDFX"] = self._find_max_price_movement_against_benchmark(benchmark_time=None, pdfx_benchmark=True)


    def _find_max_price_movement_against_benchmark(self, benchmark_time: time, pdfx_benchmark=False):
        day_objs = {}
        daily_max_pips = None
        current_date = None
        for time_index, row in self.minute_price_df.iterrows():
            current_price = PriceTime(price=row['Close'], datetime=time_index)
            if self._is_row_new_day(date=current_date, index=time_index):
                day_objs = self._save_prior_day_obj(daily_max_pips, day_objs)
                current_date = self._update_current_date(newdate=time_index)

                if pdfx_benchmark == False: 
                    benchmark_price = self._get_benchmark_price(date=time_index.date(), benchmark_time=benchmark_time)
                else: 
                    benchmark_price = self._get_prior_fix_recursive(current_date - timedelta(days=1))

                if benchmark_price is not None: 
                    daily_max_pips = self._init_new_day_obj(current_date, benchmark_price)
                else: 
                    daily_max_pips = None

            if daily_max_pips is not None:
                daily_max_pips.update_max_pip(current_price)
        
        return day_objs


    def _get_benchmark_price(self, date, benchmark_time) -> PriceTime:
        price_df = self.benchmark_prices_matrix[benchmark_time]
        index = datetime(year=date.year, month=date.month, day=date.day, hour=benchmark_time.hour, minute=benchmark_time.minute, second=0)
        price = price_df.loc[index]['Close']
        return PriceTime(price=price, datetime=index)


    def _init_new_day_obj(self, current_date: datetime.date, benchmark_pricetime: PriceTime) -> DayPipMovmentToPrice:
        return DayPipMovmentToPrice(
            date=current_date, 
            benchmark_pricetime=benchmark_pricetime,
            time_range=self.time_range)


    def _save_prior_day_obj(self, prior_day_obj: DayPipMovmentToPrice, day_objs):
        if prior_day_obj != None: 
            day_objs[prior_day_obj.date] = prior_day_obj
        return day_objs


    def _update_current_date(self, newdate: datetime) -> datetime.date:
        return newdate.date()

    
    def _is_row_new_day(self, date: datetime.date, index: datetime) -> bool:
        if date == None: 
            return True
        if index.date() != date:
            return True
        return False


    def to_string(self):
        benchmark_time_header_template = \
            "\n/********************** Benchmark Time: {} **********************/\n"
        for btime in self.max_price_movements:
            print(benchmark_time_header_template.format(btime))
            max_pips_for_btime = self.max_price_movements[btime]
            for day in max_pips_for_btime:
                day_max_pips = max_pips_for_btime[day]
                print(day_max_pips.to_string())


    def to_excel(self, fname=None):
        '''
        1. Convert to df
        2. Pass df to data_converter
        '''
        df = self._load_objs_to_df()
        data_exporter = DataWriter(df=df)
        data_exporter.df_to_xlsx()

    
    def _load_objs_to_df(self) -> pd.DataFrame:
        '''
        |------|---OHLC---|---Benchmark 1---|---Benchmark 2---|
        |------|----...---|--MaxPipUp,Down--|--MaxPipUp,Down--|
        |--T1--|
        |--T2--|
        '''
        df = pd.DataFrame()
        df.columns = pd.MultiIndex.from_product([[""], df.columns])


        benchmarked_df_list = self._generate_benchmarked_df_list()

        df = self._join_daily_price_df(target=df)
        df = self._join_benchmarked_dfs(df, benchmarked_df_list)
        df = self._join_period_avg_data(target=df)

        print(df)
        return df    

    def _generate_benchmarked_df_list(self):
        benchmarked_df_list = []
        for benchmark_time, data in self.max_price_movements.items():
            df_list = []

            for _, data_on_date in data.items():
                exported_df = data_on_date.to_df()
                df_list.append(exported_df)

            df_for_benchmark = pd.concat(df_list, sort=False)

            old_columns = df_for_benchmark.columns
            df_for_benchmark.columns = pd.MultiIndex.from_product([[str(benchmark_time)], old_columns])

            benchmarked_df_list.append(df_for_benchmark)
        return benchmarked_df_list
        

    def _join_benchmarked_dfs(self, target, benchmarked_df_list):
        # target = pd.DataFrame()
        for right_df in benchmarked_df_list:
            target = target.join(right_df, how="outer")
        return target


    def _join_daily_price_df(self, target): 
        self.daily_price_df.columns = pd.MultiIndex.from_product([["OHLC"], self.daily_price_df.columns])
        print(self.daily_price_df)
        target = target.join(self.daily_price_df)
        return target


    def _join_period_avg_data(self, target):
        price_data = read_price_data()

        df = PeriodPriceAvg(
            price_dfs=price_data, 
            time_range=TimeRangeInDay(
                start_time=time(hour=10, minute=30),
                end_time=time(hour=11, minute=2)
            ), 
            time_range_for_avg=TimeRangeInDay(
                start_time=time(hour=10, minute=55),
                end_time=time(hour=11, minute=2)
            ), 
            include_open={
                time(hour=10, minute=55),
                time(hour=10, minute=56),
            }
        ).to_df()
        df.columns = pd.MultiIndex.from_product([["1055_1102"], df.columns])
        target = target.join(df)
        return target


def read_price_data():
    in_fpaths = {
        DataReader.FIX: abspath("../data/datasrc/fix1819.csv"), 
        DataReader.MINUTELY: abspath("../data/datasrc/GBPUSD_2018.csv"),
        DataReader.DAILY: abspath("../data/datasrc/gbp_daily.xlsx")  
    }

    fx_reader = DataReader(in_fpaths)
    package = fx_reader.read_data()
    return package