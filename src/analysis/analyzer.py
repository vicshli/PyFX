from datetime import datetime
import logging
import functools
from os.path import abspath
import pandas as pd

from analysis.pricemvmts import MaxPriceMovements
from analysis.metrics import MinuteData, PeriodPriceAvg

from common.config import Config

from ds.datacontainer import DataContainer

from pyfx import read, write


logger = logging.getLogger(__name__)


class Analyzer():

    def __init__(self, config: Config):
        self.__config = config
        self.__FOLDER_TIMESTAMP = self._generate_folder_timestamp()

    def execute(self):
        pass

    def analyze_currency_pair(self, cp_name: str):
        logger.info("Initialize analysis for {}".format(cp_name))
        dataframes = {}

        # 1. Read data
        fpaths = {
            read.FIX: abspath("data/datasrc/fix1819.csv"),
            read.MINUTE: abspath("data/datasrc/GBPUSD_Candlestick.csv"),
            read.DAILY: abspath("data/datasrc/{}_Daily.xlsx".format(cp_name))
        }

        price_data = read.read_and_process_data(fpaths, cp_name)
        data_container = DataContainer(price_dfs=price_data, config=self.__config,
                                       currency_pair_name=cp_name)

        # 2. Include OHLC data
        dataframes['OHLC'] = price_data[read.DAILY]

        # 3. Include Max Pip Movements
        price_movements = MaxPriceMovements(price_data=data_container,
                                            config=self.__config,
                                            currency_pair_name=cp_name)

        price_movements.find_max_price_movements()
        price_movement_analyses = price_movements.to_benchmarked_results()
        dataframes = {**dataframes, **price_movement_analyses}

        if self.__config.should_include_minutely_data:
            # 4. Include selected minute data
            selected_minute_data = MinuteData(
                prices=data_container, config=self.__config, cp_name=cp_name
            ).to_df()
            dataframes['Selected Minute Data'] = selected_minute_data

            # 5. Include Price average data from range
            for avg_data_section in self.__config.period_average_data_sections:
                price_avg_data = PeriodPriceAvg(
                    prices=data_container, cp_name=cp_name,
                    config=self.__config, time_range_for_avg=avg_data_section
                ).to_df()
                col_name = "{}_{}".format(str(avg_data_section.start_time),
                                          str(avg_data_section.end_time))
                dataframes[col_name] = price_avg_data

        master_df = write.merge_dfs(dataframes)

        write.df_to_xlsx(df=master_df,
                         dir='data/dataout/', folder_name='dataout_',
                         fname=('dataout_{}'.format(cp_name)),
                         folder_unique_id=self.__FOLDER_TIMESTAMP,
                         sheet_name='max_pip_mvmts', col_width=20)

    def _generate_folder_timestamp(self) -> str:
        now = datetime.now()
        fname_suffix = now.strftime("_%Y%m%d_%H%M%S")
        return fname_suffix
