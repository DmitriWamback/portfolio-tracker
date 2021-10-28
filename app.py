import streamlit as st
import pandas as pd
import yfinance as yf
import datetime as dt
import plotly.graph_objects as go
import plotly.express as px


# streamlit frontend
__currency = st.selectbox(
    'Select currency *',
    ('USD','CAD','EUR')
)
__stock_type = st.selectbox(
    'Select stock type *',
    ('CRYPTO', 'STOCK')
)
__account = st.selectbox(
    'ACCOUNT *',
    ('CRYPTO', 'TFSA', 'PERS')
)
__ticker                = st.text_input('TICKER *')
__owner                 = st.text_input('OWNER *')
__date_bought           = st.text_input('DATE BOUGHT (i.e. 2000-01-01) *')
__shares_bought         = st.text_input('SHARES BOUGHT *')
__date_sold             = st.text_input('DATE SOLD (i.e. 2000-01-01)')
__shares_sold           = st.text_input('SHARES SOLD')

profit          = st.text('PROFIT: N/A')
today = dt.datetime.now().strftime("%Y-%m-%d")

# full stock trend between 2 dates
def get_stock_trend():

    full_ticker = ''
    if __stock_type == 'CRYPTO':
        full_ticker = f'{str(__ticker).upper()}-{__currency}'
    else:
        full_ticker = str(__ticker).upper()

    h = []

    if __date_sold == '':
        h = yf.download(full_ticker, __date_bought, today)

    elif __date_sold != '' and __shares_sold != '':
        h = yf.download(full_ticker, __date_bought, __date_sold)

    return h

def get_stock_price_from_date(ticker, date_bought, shares_bought):
    price = yf.download(ticker, date_bought, today)['Close'][0] * shares_bought
    print(f'ticker: {ticker}, price: {price}')
    return price

# for indexing later
FIELDS = {
    'CURRENCY':         0,
    'OWNER':            1,
    'STOCK TYPE':       2,
    'ACCOUNT':          3,
    'TICKER':           4,
    'DATE BOUGHT':      5,
    'SHARES BOUGHT':    6,
    'DATE SOLD':        7,
    'SHARES SOLD':      8
}

ACCOUNT_FIELDS = {
    'CRYPTO': 0,
    'TFSA': 1,
    'PERS': 2
}

# gets starting and ending price from the stock trend
def get_price():
    h = get_stock_trend()
    return [h['Close'][-1], h['Close'][0]]

def nonNull(critical_info: list, empty_string: bool):

    if empty_string:
        for i in critical_info:
            if i == '': return False

    else:
        for i in critical_info:
            if str(i) == 'nan': return False

    return True


def get_profit(ticker: str, date_bought: str, date_sold: str, shares_bought: float, shares_sold: float):

    if not date_sold == '' and not shares_sold == 0:

        if shares_sold < shares_bought:

            SOLD_TREND = yf.download(ticker, date_bought, date_sold)['Close']
            CURRENT_TREND = yf.download(ticker, date_bought, today)['Close']

            sold = (SOLD_TREND[-1] - SOLD_TREND[0]) * shares_sold
            current = (CURRENT_TREND[-1] - CURRENT_TREND[0]) * (shares_bought - shares_sold)

            return sold + current
        
        if shares_bought == shares_sold:
            SOLD_TREND = yf.download(ticker, date_bought, date_sold)['Close']
            return (SOLD_TREND[-1] - SOLD_TREND[0]) * shares_sold

    else:
        CURRENT_TREND = yf.download(ticker, date_bought, today)['Close']
        return (CURRENT_TREND[-1] - CURRENT_TREND[0]) * shares_bought



# splits a csv into several containing unique owners
def split_csv_by_owner(csv: pd.DataFrame) -> list:
    
    found_owners = []
    current_owners = csv['OWNER']
    last_iteration = None
    
    # finding all owners
    for owner in current_owners:

        hasFound = False

        if last_iteration != owner:
        
            for f in found_owners:
                if owner == f: hasFound = True

            if not hasFound:
                found_owners.append(owner)

        last_iteration = owner

    # getting all tickers owned by each owner
    # packaging them into new CSVs

    package = {}
    for i in range(len(found_owners)):
        owner = found_owners[i]
        dat = []
        for j in range(int(csv['OWNER'].count())):
            row = csv.values[j]
            if row[1] == owner:
                dat.append(list(row))

        package[owner] = dat
    package['all_owners'] = found_owners
    return package

# sumbit button for a single stock trend and profit
if st.button('SUBMIT'):

    historical = []
    last = 0
    paid = 0

    dat = get_price()

    trend = get_stock_trend().reset_index()
    trend_close = trend['Close']
    trend_open = trend['Open']
    trend_high = trend['High']
    trend_low = trend['Low']

    last = dat[0]
    paid = dat[1]

    if __shares_sold != '' and __date_sold != '':
        if float(__shares_sold) <= float(__shares_bought):
            pass

    _profit = float(__shares_bought) * (last - paid)

    profit.text(f'PROFIT: {_profit} {__currency}')

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend['Date'], y=trend_open, name='Stock Open'))
    fig.add_trace(go.Scatter(x=trend['Date'], y=trend_close, name='Stock Close'))
    fig.add_trace(go.Scatter(x=trend['Date'], y=trend_high, name='Stock High'))
    fig.add_trace(go.Scatter(x=trend['Date'], y=trend_low, name='Stock Low'))
    fig.layout.update(title_text='Stock Trend', xaxis_rangeslider_visible=True)

    st.plotly_chart(fig)

# appending form data into data/save.csv
if st.button('SAVE'):
    
    critical_information = [__ticker, __owner, __date_bought, __shares_bought, __account, __stock_type, __currency]
    if nonNull(critical_information, True):
        if __date_sold != '' and __shares_sold != '':
            data = f'USD,{__owner},{__stock_type},{__account},{__ticker},{__date_bought},{__shares_bought},{__date_sold},{__shares_sold}\n'
            with open('data/save.csv', 'a+') as file:
                file.write(data)

        else:
            data = f'USD,{__owner},{__stock_type},{__account},{__ticker},{__date_bought},{__shares_bought},NULL,NULL\n'
            with open('data/save.csv', 'a+') as file:
                file.write(data)



if st.button('LOAD'):
    all_data = pd.read_csv('data/save.csv')
    st.dataframe(all_data)



if st.button('CALCULATE ALL PROFITS'):
    all_data = pd.read_csv('data/save.csv')
    investments_data = pd.read_csv('data/investments.csv')
    package = split_csv_by_owner(all_data)

    dat = []

    owners = package['all_owners']
    for o in owners:
        pack = package[o]
        pack_len = len(pack)
        owner = o
        all_profits = ['', 0, 0, 0, 0] # owner, investments, crypto, tfsa, pers
        all_profits[0] = owner

        prices = [0, 0, 0]

        for i in range(pack_len):
            # getting all necessary information
            date_bought     = pack[i][FIELDS['DATE BOUGHT']]
            date_sold       = pack[i][FIELDS['DATE SOLD']]
            shares_bought   = pack[i][FIELDS['SHARES BOUGHT']]
            shares_sold     = pack[i][FIELDS['SHARES SOLD']]
            account         = pack[i][FIELDS['ACCOUNT']]
            ticker          = pack[i][FIELDS['TICKER']]

            __acc_id = ACCOUNT_FIELDS[account]
            
            full_ticker = ticker
            if account == 'CRYPTO': full_ticker = f'{full_ticker}-USD'

            print(full_ticker)

            if nonNull([date_sold, shares_sold], False):
                prices[__acc_id] = prices[__acc_id] + get_profit(full_ticker, date_bought, date_sold, float(shares_bought), float(shares_sold))

            else:
                prices[__acc_id] = prices[__acc_id] + get_profit(full_ticker, date_bought, '', shares_bought, 0)


            currency = __currency

            if str(date_sold) == 'nan':
                all_profits[1] = all_profits[1] + get_stock_price_from_date(full_ticker, date_bought, shares_bought)
            all_profits[__acc_id+2] = prices[__acc_id]

        all_profits[1] = all_profits[1] / yf.download('CADUSD=X', date_bought, today)['Close'][-1]
        dat.append(all_profits)
    print(dat)

    
    df = pd.DataFrame(
        dat,
        columns=['Owner', 'INVESTMENTS', 'CRYPTO', 'TFSA', 'PERSONAL',]
    )
    print(df)
    
    # plotting data
    fig = px.bar(df, x='Owner', y=['INVESTMENTS', 'CRYPTO', 'TFSA', 'PERSONAL'])
    st.plotly_chart(fig)
