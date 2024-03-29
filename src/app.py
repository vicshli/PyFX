"""
This file is the starting point of the program. It provides a bird's eye view
of the operations carried out to generate key metrics and to export to excel.
"""

import logging
from datetime import datetime
from os.path import abspath

import pandas as pd

from common.config import Config
from common.decorators import timer
from common import utils
from common.utils import run
from ds.datacontainer import DataContainer
from pyfx import analytics, read, write

try:
    logging.config.fileConfig(utils.get_logger_config_fpath())
except FileNotFoundError as e:
    print(e)
logger = logging.getLogger(__name__)


def io(func):
    """Decorator that abstracts the currency data input-output logic.

    Performs data files input (loading from csv and xlsx files) for the 
    decorated function to consume, and writes a xlsx file containing the 
    decorated function's output.

    Raises
    ------

    """

    def wrapper(*args, **kwargs):
        REQUIRED_ARGS = ['cp_name', 'config', 'folder_suffix']
        if any(k not in kwargs for k in REQUIRED_ARGS):
            raise IOParamParsingError((
                "@io argument parsing error.\n\nSome of the following required "
                f"keyword arguments are missing: \n\t{REQUIRED_ARGS}.\n"
                "Note that these arguments must be passed in as kwargs.\n"
            ))

        cp_name = kwargs.get('cp_name')
        config = kwargs.get('config')
        suffix = kwargs.get('folder_suffix')

        logger.info(f"Processing currency pair {cp_name}")

        fpaths = config.fpath(cp_name)

        dfs = read.read_data(fpaths, cp_name=cp_name)
        data = DataContainer(dfs, cp_name, config)

        df_master = func(*args, **kwargs, data=data)

        write.df_to_xlsx(df=df_master,
                         dir='data/dataout/', folder_name='dataout_',
                         fname=('dataout_{}'.format(cp_name)),
                         folder_unique_id=suffix,
                         sheet_name='max_pip_mvmts', col_width=20)
    return wrapper


class IOParamParsingError(Exception):
    """Raised when not all params required by the @io decorator can be located.
    """
    pass


@io
def exec(cp_name: str, config: Config, folder_suffix: str, **kwargs):

    data = kwargs.get('data')

    output_funcs = [
        run(analytics.include_ohlc, data),
        run(analytics.include_max_pips, data, config.benchmark_times),
        run(analytics.include_max_pips, data, pdfx=True, cp_name=cp_name),
        run(analytics.include_minute_data, data, config.minutely_data_sections),
        run(analytics.include_avgs, data, config.period_average_data_sections)
    ]

    outputs = map(lambda f: f(), output_funcs)

    df_master = pd.concat(outputs, axis=1)
    df_master.index = df_master.index.date

    return df_master


@timer
def main():
    config = Config(utils.get_app_config_fpath())
    folder_suffix = utils.folder_timestamp_suffix()

    for cp in config.currency_pairs:
        exec(cp_name=cp, config=config, folder_suffix=folder_suffix)


if __name__ == '__main__':
    main()
