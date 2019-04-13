import os
import pandas as pd
from datetime import datetime


class DataWriter:

    def __init__(self, df, currency_pair_name: str, timestamp: str, filename="../data/dataout/"):
        self._df = df
        self._default_fname = filename + "dataout_{}".format(timestamp)

        if not os.path.exists(self._default_fname):
            os.makedirs(self._default_fname)

        self._default_fname_xlsx = self._default_fname + \
            '/dataout_' + currency_pair_name + ".xlsx"

        self._default_fname_csv = currency_pair_name + '/dataout_' + \
            currency_pair_name + self._default_fname + ".csv"

    def df_to_xlsx(self):
        with pd.ExcelWriter(self._default_fname_xlsx, engine='xlsxwriter') as writer:
            self._df.to_excel(writer, sheet_name="max_pip_mvmts")
            sheet = writer.sheets['max_pip_mvmts']
            wide_col = 20
            sheet.set_column(0, len(self._df.columns), wide_col)
