from util import *
import matplotlib.pyplot as plt
import numpy as np
import argparse

# Apply basic statistical analysis to find NFTs in collection that may be
# undervalued compared to listing price 

plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.top'] = False

parser = argparse.ArgumentParser()
parser.add_argument('-contract', type=str, help='contract address to get NFT metadata', required=True)
args = parser.parse_args()

contract = args.contract

slug = get_slug(contract)

def get_fair_value_for_token(token_id, rankings, sales):
    rarity = rankings.loc[token_id].rarity

    max_dist = 0.05 * rarity
    distance = abs(sales[sales.index != token_id]['rarity'] - rarity)
    cluster_idx = distance[distance <= max_dist].index
    cluster = sales.loc[cluster_idx]

    fair_value = cluster['last_sale_price'].mean()
    cluster_size = len(cluster)

    return fair_value, cluster_size


print('Getting data for collection {}...'.format(slug))

df = get_rankings_prices(slug)

df.to_csv('data/{}.csv'.format(slug))

sales = get_last_sales(df, 48)

print('{} total sales in the last 48 hours.'.format(len(sales)))

sales = sales[['rank', 'rarity', 'last_sale_price']]

listings = df[['rank', 'rarity', 'price']].dropna()

fair_value = []
cluster_size = []

for token_id in listings.index:
    fv, cs = get_fair_value_for_token(token_id, df, sales)
    fair_value.append(fv)
    cluster_size.append(cs)

listings['fair_value'] = fair_value
listings['cluster_size'] = cluster_size
listings['price_difference'] = listings['fair_value'] - listings['price']

listings = listings[listings['cluster_size'] >= 5].sort_values(by='price_difference', ascending=False)

print(listings)

x = sales['rarity']
y = sales['last_sale_price']
f = np.poly1d(np.polyfit(x, y, 1))

plt.scatter(x, y, marker='.', color='black')
plt.plot(x, f(x), color='green', linewidth=1)

plt.title(slug)
plt.xlabel('rarity')
plt.ylabel('sale price')

plt.show()
plt.clf()
