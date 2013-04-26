#!/usr/bin/env python
import mexbtcapi
from mexbtcapi.concepts.currencies import USD,BTC
from mexbtcapi.concepts.currency import Amount, ExchangeRate
from mexbtcapi.concepts.market import Order

import matplotlib.pyplot as plt


dollars= "100000"*USD
for api in mexbtcapi.apis:
#    try:
        market = api.market(USD)
        print market.simulateOrder(Order(market, None, Order.BID, dollars, ExchangeRate(BTC, USD, 150)))

#    except Exception, e:
        print "Failed to use "+api.name 
