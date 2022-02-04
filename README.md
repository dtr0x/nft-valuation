# nft-valuation
An application to compute a rarity score for NFTs and compare with their listing price.

**Note**: This code is configured to use the legacy OpenSea API (no key required). Some endpoints now require a key, breaking functionality. The data pulled from this API can also contain errors, so it may be better to rewrite this codebase using on-chain data from an indexing service (such as Covalent) or directly from an Ethereum archive node.

### Requirements
```
- pandas
- numpy
- requests
- matplotlib
- ipfs daemon (if you plan to download metadata using get_ipfs_metadata.sh)
```

### Description
The program can be used for downloading the metadata ("traits") for an NFT collection given the contract address. We can then compute rarity scores which is done  via the "trait normalization" technique used by, for example, https://rarity.tools/. Inspect the code of ```get_rarity_score``` and related functions in ```util.py``` to understand my implementation. By comparing the listing price on OpenSea with each item's rarity, a scalar metric "rarity-price ratio" can be found for each listing. The items with the highest rarity-price ratio  have the lowest price per unit of rarity, which could potentially indicate a buying opportunity.

**Note**: This code is just for experimental purposes, nothing here constitutes financial advice. There is no guarantee that the rarity based on trait frequency is indicative of value. Many NFT collections have traits with special properties that may not be captured by the simple scoring method used here. A better method would be a supervised learning approach using traits and sales data, but this may not be feasible due to limited volume of the highest value items from a collection.


### Usage
To analyze a particular NFT collection, you first must obtain the metadata. Pulling this from OpenSea can sometimes contain errors (although would make this code more consistent). As an example, a script is provided to get the metadata via an IPFS endpoint, which is often present in the ```TokenURI``` of the contract code. If using IPFS, the hash location can be found here. The full metadata can then be downloaded using 
```
> ./get_ipfs_metadata.sh <ipfs_hash> <opensea_collection_slug>
```
This is just an example, and will not always work. It is important to have the correct slug name as it will be used later, you can get this from ```get_slug``` in util.py. Note that you must have an ipfs daemon running to execute this script.

Once metadata is obtained, to compute rarities, pull price from OpenSea, and sort by rarity-price ratios, simply run 
```
> python rarity_price.py -contract=<contract_address>
```
which will save a CSV in the data folder. 

An alternative, which employs a basic mean-clustering algorithm to get a "fair value" for each token can be found via
```
> python get_fair_value.py -contract=<contract_address>
```



