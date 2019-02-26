import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
import xlsxwriter


c_mpip_up_1030 = 'MAX_PIP_UP_1030'
c_mpip_up_1045 = 'MAX_PIP_UP_1045'
c_mpip_up_1030_dt = "MAX_PIP_UP_1030_DATETIME"
c_mpip_up_1045_dt = "MAX_PIP_UP_1045_DATETIME"
c_mpip_up_1030_pr = "MAX_PIP_UP_1030_PRICE"
c_mpip_up_1045_pr = "MAX_PIP_UP_1045_PRICE"

c_mpip_dn_1030 = 'MAX_PIP_DOWN_1030'
c_mpip_dn_1045 = 'MAX_PIP_DOWN_1045'
c_mpip_dn_1030_dt = "MAX_PIP_DOWN_1030_DATETIME"
c_mpip_dn_1045_dt = "MAX_PIP_DOWN_1045_DATETIME"
c_mpip_dn_1030_pr = "MAX_PIP_DOWN_1030_PRICE"
c_mpip_dn_1045_pr = "MAX_PIP_DOWN_1045_PRICE"

c_ls_1030 = '1030_LS'
c_ls_1045 = '1045_LS'
c_1030_pr = '1030_PRICE'
c_1045_pr = '1045_PRICE'
c_1102_pr = '1102_CLOSE'


pipmvmt = lambda final, initial: (final - initial) * 10000

is_same_date = lambda d1, d2: (d1.year == d2.year) \
    and (d1.month == d2.month) and (d1.day == d2.day)

days_against_pip_mvmt = lambda df, pipmvmt: df.query(\
    '{} < pip & pip < 0'.format(pipmvmt))

init_mpip = lambda p1030, p1045, dt1030, dt1045: { 
        c_1030_pr: p1030, 
        c_1045_pr: p1045, 

        c_mpip_up_1030: 0,
        c_mpip_up_1045: 0,
        c_mpip_up_1030_dt: dt1030,
        c_mpip_up_1045_dt: dt1045,
        c_mpip_up_1030_pr: p1030,
        c_mpip_up_1045_pr: p1045,

        c_mpip_dn_1030: 0,
        c_mpip_dn_1045: 0,
        c_mpip_dn_1030_dt: dt1030,
        c_mpip_dn_1045_dt: dt1045,
        c_mpip_dn_1030_pr: p1030,
        c_mpip_dn_1045_pr: p1045,
    }

init_ls = lambda: {
        c_ls_1030: 'N/A',
        c_ls_1045: 'N/A',
        c_1030_pr: 'N/A',
        c_1045_pr: 'N/A',
        c_1102_pr: 'N/A'
    }

def csv_in(fpath):
    df = pd.read_csv(fpath)

    df.columns = ["date", "time", "val", "B", "C", "D", "E"]
    df = df.drop(columns=['B', 'C', 'D', 'E'])

    df['datetime'] = df["date"].map(str) + " " + df["time"] 
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["date"] = pd.to_datetime(df["date"]) 
    df = df.set_index('datetime')
    df = df[['date', 'time', 'val']]
    df = df.drop(columns=['time', 'date'])

    return df


def proc_df():
    cur_date = None
    p1030 = None
    p1045 = None
    mpip = {}  
    ls = {}  
    
    for date_minute, row in mdf.iterrows():

        if date_minute.date() != cur_date:
            cur_date = date_minute.date()
            dt1030 = str(cur_date) + " 10:30:00"
            dt1045 = str(cur_date) + " 10:45:00"
            p1030 = df_1030.loc[dt1030]['val']
            p1045 = df_1045.loc[dt1045]['val']
            mpip[cur_date] = init_mpip(p1030, p1045, dt1030, dt1045)
            ls[cur_date] = init_ls()

        cur_pr = row['val']

        cur_pip_1030 = pipmvmt(cur_pr, p1030)
        cur_pip_1045 = pipmvmt(cur_pr, p1045)

        handle_mpip(cur_pip_1030, mpip, cur_date, date_minute, cur_pr, cur_pip_1045)

        if str(date_minute) == str(cur_date) + " 11:02:00":
            handle_ls(p1030, ls, cur_date, p1045, row)

    return mpip, ls


def handle_mpip(cur_pip_1030, mpip, cur_date, date_minute, cur_pr, cur_pip_1045):
    if cur_pip_1030 > mpip[cur_date][c_mpip_up_1030]:
        mpip[cur_date][c_mpip_up_1030] = cur_pip_1030
        mpip[cur_date][c_mpip_up_1030_dt] = date_minute
        mpip[cur_date][c_mpip_up_1030_pr] = cur_pr
    if cur_pip_1045 > mpip[cur_date][c_mpip_up_1045]:
        mpip[cur_date][c_mpip_up_1045] = cur_pip_1045
        mpip[cur_date][c_mpip_up_1045_dt] = date_minute
        mpip[cur_date][c_mpip_up_1045_pr] = cur_pr

    if cur_pip_1030 < mpip[cur_date][c_mpip_dn_1030]:
        mpip[cur_date][c_mpip_dn_1030] = cur_pip_1030
        mpip[cur_date][c_mpip_dn_1030_dt] = date_minute
        mpip[cur_date][c_mpip_dn_1030_pr] = cur_pr
    if cur_pip_1045 < mpip[cur_date][c_mpip_dn_1045]:
        mpip[cur_date][c_mpip_dn_1045] = cur_pip_1045
        mpip[cur_date][c_mpip_dn_1045_dt] = date_minute
        mpip[cur_date][c_mpip_dn_1045_pr] = cur_pr


def handle_ls(p1030, ls, cur_date, p1045, row):
    p1102 = row['val']
    ls[cur_date][c_1030_pr] = p1030
    ls[cur_date][c_1045_pr] = p1045
    ls[cur_date][c_1102_pr] = p1102
    if p1102 > p1030:
        ls[cur_date][c_ls_1030] = 'LONG'
    elif p1102 < p1030:
        ls[cur_date][c_ls_1030] = 'SHORT'
    else:
        ls[cur_date][c_ls_1030] = 'PAR'
    if p1102 > p1045:
        ls[cur_date][c_ls_1045] = 'LONG'
    elif p1102 < p1045:
        ls[cur_date][c_ls_1045] = 'SHORT'
    else:
        ls[cur_date][c_ls_1045] = 'PAR'


def ls_to_df(ls):
    df_ls = pd.DataFrame.from_dict(ls, orient='index')
    df_ls = df_ls[[c_ls_1030, c_1030_pr, \
        c_ls_1045, c_1045_pr, c_1102_pr]]
    return df_ls


def mpip_to_df(mpip):
    df_mpip = pd.DataFrame.from_dict(mpip, orient='index')
    df_mpip = df_mpip[[
        c_1030_pr, 
        c_mpip_up_1030, c_mpip_up_1030_pr, c_mpip_up_1030_dt, 
        c_mpip_dn_1030, c_mpip_dn_1030_pr, c_mpip_dn_1030_dt, 
        c_1045_pr,
        c_mpip_up_1045, c_mpip_up_1045_pr, c_mpip_up_1045_dt, 
        c_mpip_dn_1045, c_mpip_dn_1045_pr, c_mpip_dn_1045_dt, 
    ]]
    return df_mpip


def daily_pip_mvmt():
    pipmvmts = {}
    for date, row in df_1102.iterrows():
        close_price = row['val']
        open_price = df_1030.loc[str(date.date()) + ' 10:30:00']['val']
        pipmvmts[date.date()] = { 
            'pip': pipmvmt(close_price, open_price), 
            'open': open_price, 
            'close': close_price
        }
    return pipmvmts


def df_to_xls(df, fname):
    with pd.ExcelWriter(fname, engine='xlsxwriter') as writer: 
        df.to_excel(writer, sheet_name="max_pip_mvmts")
        sheet = writer.sheets['max_pip_mvmts']
        sheet.set_column(0, len(df.columns), 18)


def pip_mvmt_to_excel(df_pip, mvmts):
    with pd.ExcelWriter('2018_daily_pip_mvmts.xlsx', engine='xlsxwriter') as writer: 
        df_pip.to_excel(writer, sheet_name='all_daily_pip_mvmts')
        for pip_mvmt in mvmts: 
            df = days_against_pip_mvmt(df_pip, pip_mvmt)
            df.to_excel(writer, sheet_name='{} pips'.format(pip_mvmt))


def main():
    global mdf, df_1030, df_1045, df_1102
    df = csv_in("GBPUSD_2018.csv")
    mdf = df.between_time('10:30', '11:02')
    df_1030 = df.between_time('10:30', '10:30')
    df_1045 = df.between_time('10:45', '10:45')
    df_1102 = df.between_time('11:02', '11:02')

    # print(mdf)

    mpip, ls = proc_df()
    df_mpip = mpip_to_df(mpip)
    df_ls = ls_to_df(ls)
    df_to_xls(df_mpip, '18mpip.xlsx')

    daily_pip = daily_pip_mvmt()
    df_daily_pip = pd.DataFrame.from_dict(daily_pip, orient='index')

    pip_neg3 = days_against_pip_mvmt(df_daily_pip, -3)
    pip_neg4 = days_against_pip_mvmt(df_daily_pip, -4)
    pip_neg5 = days_against_pip_mvmt(df_daily_pip, -5)
    pip_neg6 = days_against_pip_mvmt(df_daily_pip, -6)
    print("less than 3 pips: {} days".format(len(pip_neg3)))
    print("less than 4 pips: {} days".format(len(pip_neg4)))
    print("less than 5 pips: {} days".format(len(pip_neg5)))
    print("less than 6 pips: {} days".format(len(pip_neg6)))

    pip_mvmt_to_excel(df_daily_pip, [-3, -4, -5, -6])


if __name__ == '__main__':
    main()
