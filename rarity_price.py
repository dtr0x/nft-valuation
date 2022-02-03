from util import *
import argparse

# Compute rarity and rarity-price-ratio for each listed NFT in collection

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-contract', type=str, help='contract address to get NFT metadata', required=True)
    args = parser.parse_args()

    contract = args.contract

    slug = get_slug(contract)

    print('Getting data for collection {}...'.format(slug))

    df = get_rankings_prices(slug)

    df.to_csv('data/{}.csv'.format(slug))
