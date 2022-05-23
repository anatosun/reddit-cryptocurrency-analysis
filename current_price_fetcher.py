# First import the libraries that we need to use
import pandas as pd
import requests
import json
import time


class CurrentPriceFetcher():
    
    def __init__(self):
        pass

    def fetch_daily_data(self, symbol, start):
        #fetches 24h-1s from start in 5 min intervals
        pair_split = symbol.split('/')  # symbol must be in format XXX/XXX ie. BTC/EUR
        symbol = pair_split[0] + '-' + pair_split[1]
        end = start + 60*60*24 - 1
        url = f'https://api.pro.coinbase.com/products/{symbol}/candles?granularity=300&start={start}&end={end}'
        response = requests.get(url)
        if response.status_code == 200:  # check to make sure the response from server is good
            data = pd.DataFrame(json.loads(response.text), columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
            data['date'] = pd.to_datetime(data['unix'], unit='s')  # convert to a readable date
            data['vol_fiat'] = data['volume'] * data['close']      # multiply the BTC volume by closing price to approximate fiat volume

            # if we failed to get any data, print an error...otherwise write the file
            if data is None:
                 print("Did not return any data from Coinbase for this symbol")
            else:
                 #data.to_csv(f'Coinbase_{pair_split[0] + pair_split[1]}_dailydata.csv', index=False)
                return data
        else:
            print(response.status_code)
            print("Did not receieve OK response from Coinbase API")


    def fetch_n_days(self, symbol, start, days):
        l = []
        for i in range(0,days):
            s = start+i*24*60*60
            
            print(s, time.time())
            if s > time.time():
                #l.append(self.fetch_daily_data(symbol, s))
                break

            print(f'fetching: day {i} for {symbol}')
            l.append(self.fetch_daily_data(symbol, s))
            time.sleep(1)

        return pd.concat(l)
    
    def dump_symbols(self, symbols, start, days, path):
        for symbol in symbols:
            start_date = pd.to_datetime(start, unit='s')
            file = f"{symbol.replace('/', '-')}-{start_date.strftime('%Y-%m-%d')}.csv"
            m = self.fetch_n_days(symbol, start, days).sort_values(by='unix').reset_index(drop=True)
            m.index.name = 'index'
            m.to_csv(path+file)




if __name__ == "__main__":
    fetcher = CurrentPriceFetcher()

    start = 1648771200 #1.4.22 00:00
    fetcher.dump_symbols(['BTC/USD', 'ETH/USD', 'DOGE/USD'], start, 100, './data/price/')    
