#!/bin/bash

# Usage:
# $1 := ipfs hash to locate metadata
# $2 := opensea slug name for collection

for i in {0..9999};
  do ipfs get $1/$i -o metadata/$2/$i.json;
done
