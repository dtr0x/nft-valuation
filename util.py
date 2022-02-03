import numpy as np
import pandas as pd
import requests, time, json, os
import datetime

# pandas display options
pd.set_option('display.max_rows', 10000)
pd.set_option('display.float_format', lambda x: '%.6f' % x)

OPENSEA_API_URL = 'https://api.opensea.io/api/v1/'


# pretty print a dictionary
def pprint(dict_data):
    print(json.dumps(dict_data, sort_keys=True, indent=4))


# request function (prevents throttling)
def request_wrapper(endpoint, params={}):
    try:
        return requests.get(OPENSEA_API_URL + endpoint, params=params)
    except:
        print('Request error. Retrying in 90 seconds...')
        time.sleep(90)
        return request_wrapper(func, kwargs)


# get collection slug via contract address
def get_slug(contract):
    r = request_wrapper('asset_contract/{}'.format(contract.lower()))
    return r.json()['collection']['slug']


# get token traits from json files in directory
def get_token_traits_from_files(dirname):
    path = 'metadata/{}'.format(dirname)
    metadata_files = os.listdir(path)
    traits = []

    for m in metadata_files:
        with open(path + '/' + m) as f:
            try:
                a = json.load(f)
            except json.decoder.JSONDecodeError:
                print(m)
                return

        t = a['attributes']
        k = [x['trait_type'] for x in t]
        v = [x['value'] for x in t]
        t = dict(zip(k,v))
        t['token_id'] = m.split('.')[0]
        traits.append(t)

    # return the DataFrame
    traits = pd.DataFrame(traits)
    traits = traits.set_index('token_id')
    traits.index = traits.index.astype('int')
    traits = traits.sort_values(by='token_id')
    traits = traits.fillna('None') #.drop(columns='Serial')

    # add trait count
    f = lambda x: len(x[x != 'None'])
    traits['trait_count'] = traits.agg(f, axis=1)

    return traits


# get all token traits from collection
def get_token_traits(slug):
    has_assets = True
    traits = []
    prices = []
    sales = []
    i = 0

    # cycle through collection storing traits for each token id
    while(has_assets):
        params = {'order_by': 'pk', 'order_direction': 'asc', 'offset': i, 'limit': 50, 'collection': slug}
        r = request_wrapper('assets', params).json()
        if 'assets' in r.keys() and len(r['assets']) > 0:
            assets = r['assets']

            for a in assets:

                # get the price if available
                if 'sell_orders' in a.keys() and a['sell_orders']:
                        s = a['sell_orders'][0]
                        base_price = round(int(s['base_price']) * 1e-18, 2)
                        is_eth = (s['payment_token_contract']['id'] == 1)
                        if base_price > 0 and is_eth:
                            prices.append((a['token_id'], base_price))


                # get last sale price and timestamp
                if 'last_sale' in a.keys() and a['last_sale']:
                    s = a['last_sale']
                    # only include ETH and WETH sales
                    if s['payment_token']['id'] in [1,2]:
                        last_sale_price = round(int(s['total_price']) * 1e-18, 2)
                        last_sale_time = s['event_timestamp']
                        sales.append((a['token_id'], last_sale_price, last_sale_time))


            i += 50
        else:
            has_assets = False

    # traits DataFrame
    traits = get_token_traits_from_files(slug)

    # prices DataFrame
    prices = pd.DataFrame(prices)
    prices.columns = ['token_id', 'price']
    prices = prices.set_index('token_id')
    prices.index = prices.index.astype('int')

    # sales DataFrame
    sales = pd.DataFrame(sales)
    sales.columns = ['token_id', 'last_sale_price', 'last_sale_time']
    sales = sales.set_index('token_id')
    sales.index = sales.index.astype('int')
    # convert to local time
    sales['last_sale_time'] = pd.to_datetime(sales['last_sale_time'], format='%Y-%m-%dT%H:%M:%S') - pd.Timedelta(4, 'hours')

    return traits, prices, sales


# get last sales from 'hours' ago
def get_last_sales(sales, hours):
    t = datetime.datetime.now() - datetime.timedelta(hours=hours)
    return sales[sales['last_sale_time'] >= t]


# replace trait values in trait dataframe with normalized rarity score
def get_trait_rarity(traits):
    trait_rarity_dict = {col: len(traits)/traits[col].value_counts() for col in traits.columns}
    trait_rarity_dict_counts = {k:len(trait_rarity_dict[k]) for k in trait_rarity_dict.keys()}
    trait_rarity_dict = {k:trait_rarity_dict[k]/trait_rarity_dict_counts[k] for k in trait_rarity_dict.keys()}
    trait_rarity = traits.copy()

    for col in trait_rarity.columns:
        trait_rarity[col] = [trait_rarity_dict[col][a] for a in trait_rarity[col]]

    return trait_rarity


# sum trait rarity values and return normalized rarity score and rank
def get_rarity_score(trait_rarity):
    score = trait_rarity.agg(np.sum, axis=1).to_frame()
    score.columns = ['rarity']
    score = score.sort_values(by='rarity', ascending=False)
    score['rank'] = range(1, len(score)+1)
    score = score[['rank', 'rarity']]
    return score


# merge score and trait dataframes
def get_rankings(traits):
    rarity = get_trait_rarity(traits)
    score = get_rarity_score(rarity)
    df = traits.join(score)
    cols = list(df.columns[-2:]) + list(df.columns[:-2])
    return df[cols].sort_values(by='rank')


# get all traits and rarity rankings for contract with price
def get_rankings_prices(slug):
    traits, prices, sales = get_token_traits(slug)
    rankings = get_rankings(traits).join(prices)

    # rarity price ratio
    rankings['rpr'] = rankings['rarity']/rankings['price']

    cols = list(rankings.columns)
    cols_ord = cols[:2] + cols[-2:] + cols[2:-2]
    rankings = rankings[cols_ord].join(sales)
    return rankings


# load the DataFrame by slug
def load_frame(slug):
    df = pd.read_csv('data/{}.csv'.format(slug), index_col='token_id', parse_dates=['last_sale_time'])
    return df
