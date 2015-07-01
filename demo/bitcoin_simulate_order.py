#!/usr/bin/env python
import mexbtcapi
from mexbtcapi.concepts.currencies import USD,BTC
from mexbtcapi.concepts.currency import Amount, ExchangeRate
from mexbtcapi.concepts.market import Order

import matplotlib.pyplot as plt


dollars= "1000"*USD
bitcoins = "500"*BTC
for api in mexbtcapi.apis:
    try:
        market = api.market(USD)
        print "Using market:", market.name
        print "bid BTC: ", market.simulateOrder(Order(market, None, Order.BID, bitcoins, ExchangeRate(BTC, USD, 150)))
        print "bid USD: ", market.simulateOrder(Order(market, None, Order.BID, dollars, ExchangeRate(BTC, USD, 150)))
        print "ask USD: ", market.simulateOrder(Order(market, None, Order.ASK, dollars, ExchangeRate(BTC, USD, 100)))
        print "ask BTC: ", market.simulateOrder(Order(market, None, Order.ASK, bitcoins, ExchangeRate(BTC, USD, 100)))
        print "buy market USD: ", market.simulateOrder(Order(market, None, Order.MARKET_BUY, dollars, None))
        print "sell market USD: ", market.simulateOrder(Order(market, None, Order.MARKET_SELL, dollars, None))
        print "---"*20

    except Exception, e:
        print "Failed to use "+api.name 
        raise
