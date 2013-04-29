#!/usr/bin/env python
import mexbtcapi
from mexbtcapi.concepts.currencies import USD,BTC
from mexbtcapi.concepts.currency import Amount, ExchangeRate
from mexbtcapi.concepts.market import Order

import matplotlib.pyplot as plt


dollars= "1000"*USD
bitcoins = "500"*BTC
for api in mexbtcapi.apis:
#    try:
        market = api.market(USD)
        print market.simulateOrder(Order(market, None, Order.BID, bitcoins, ExchangeRate(BTC, USD, 150)))
        print market.simulateOrder(Order(market, None, Order.BID, dollars, ExchangeRate(BTC, USD, 150)))
        print market.simulateOrder(Order(market, None, Order.ASK, dollars, ExchangeRate(BTC, USD, 100)))
        print market.simulateOrder(Order(market, None, Order.ASK, bitcoins, ExchangeRate(BTC, USD, 100)))
        print market.simulateOrder(Order(market, None, Order.MARKET_BUY, dollars, None))
        print market.simulateOrder(Order(market, None, Order.MARKET_SELL, dollars, None))

#    except Exception, e:
        print "Failed to use "+api.name 
        raise Exception()
