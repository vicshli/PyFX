from os.path import abspath
from datetime import datetime, time 

from dataio.datareader import DataReader
from datastructure.daytimerange import TimeRangeInDay
from maxpricemvmts import MaxPriceMovements
from periodpriceavg import PeriodPriceAvg
from dfbundler import DataFrameBundler
from dataio.datawriter import DataWriter

def main():
    start_time = datetime.now()

    price_data = read_price_data()

    price_movements = setup_price_movement_obj(data=price_data)
    price_movements.find_max_price_movements()
    # print(price_movements.to_string())
    price_movements.to_excel()


    end_time = datetime.now()
    print("Program runtime: {}".format((end_time - start_time)))
    

def setup_price_movement_obj(data):

    pip_movement_config = {
        MaxPriceMovements.TIME_RANGE: TimeRangeInDay(
            start_time=time(hour=10, minute=30),
            end_time=time(hour=11, minute=2)
        ),
        MaxPriceMovements.BENCHMARK_TIMES: [
            time(hour=10, minute=30), time(hour=10, minute=45)
        ],
    }

    return MaxPriceMovements(price_dfs=data, config=pip_movement_config)

    # return init_pip_movement_obj(price_data=package)


def read_price_data():
    in_fpaths = {
        DataReader.FIX: abspath("../data/datasrc/fix1819.csv"), 
        DataReader.MINUTELY: abspath("../data/datasrc/GBPUSD_2018.csv"),
        DataReader.DAILY: abspath("../data/datasrc/gbp_daily.xlsx")  
    }

    fx_reader = DataReader(in_fpaths)
    package = fx_reader.read_data()
    return package



if __name__ == '__main__':
    main()