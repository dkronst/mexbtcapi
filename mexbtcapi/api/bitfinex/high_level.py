#!/usr/bin/env python

"""
Implements the High-level API for Bitfinex so that it can be used 
with the mexbtcapi package
"""

import logging

from mexbtcapi import concepts
from mexbtcapi.concepts.currencies import *
from mexbtcapi.concepts.currency import Amount, Currency, ExchangeRate
from mexbtcapi.concepts.market import ActiveParticipant, Market as BaseMarket, Order, Trade

from decimal import Decimal

logger = logging.getLogger(__name__)


class BitfinexTicker(concepts.market.Ticker):
    def __repr__(self):
        return \
            "<BitfinexTicker({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8})" \
            .format(self.market, self.time, self.high, self.high, self.last,
            self.volume, self.average, self.buy, self.sell)


class BitfinexOrder(Order):
    def __init__(self, oid, *args, **kwargs):
        super(BitfinexOrder, self).__init__(*args, **kwargs)
        self.oid = oid

    def __repr__(self):
        return \
            "<BitfinexOrder({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}>" \
            .format(self.market, self.timestamp, self.oid, self.buy_or_sell,
            self.from_amount, self.exchange_rate, self.properties, self.entity)


class BitfinexMarket(BaseMarket):
    MARKET_NAME = "Bitfinex"

    def __init__(self, currency, item = BTC, depth = 50):
        try:
            from bitfinex.client import Client
        except ImportError:
            print "Couldn't find module bitfinex. Download and install from:"
            print "https://github.com/scottjbarr/bitfinex"
            print "Or run:\n pip install bitfinex"
            sys.exit(1)
            
        super(BitfinexMarket, self).__init__(self.MARKET_NAME, currency, item)
        self.client = Client()
        self.depth = depth

    def getTicker(self):
        logger.debug("getting ticker")

        raise NotImplementedError()

    def _getCurrencyPair(self):
        return "%s%s"%(self.currency2.name.lower(), self.currency1.name.lower())

    def getDepth(self):
        logger.debug("getting depth")

        parameters = {'limit_asks': self.depth, 'limit_bids': self.depth}
        
        d = self.client.order_book(self._getCurrencyPair(), parameters)

        ret = {
            'asks': self._depthToOrders(d[u'asks'], Order.ASK),
            'bids': self._depthToOrders(d[u'bids'], Order.BID),
        }
        return ret

    def _depthToOrders(self, depth, order_type):
        from datetime import datetime
        orders = []

        for d in depth:
            # TODO: change the low-level stream to use Amount instead of numbers
            # this means also changing the "hash" of Amount.
            amount = Amount(Decimal(d[u'amount']), self.currency2)
            price = ExchangeRate(self.currency2, self.currency1, Decimal(d[u'price']))
            order = Order(self, datetime.fromtimestamp(d[u'timestamp']), order_type, amount, price)
            orders.append(order)

        return orders


class BitfinexParticipant(ActiveParticipant):

    def __init__(self, market, key, secret, nonce):
        super(BitfinexParticipant, self).__init__(market)
        self.private = low_level.Private(key, secret)

    def placeOrder(self, order):
        """places an Order in the market for limit/amount"""
        now = datetime.now()
        if order.is_bid_order():
            logger.debug("placing bid order")
            oid = self.private.bid(order.from_amount.value, order.exchange_rate)
            return BitfinexOrder(oid, self.market, now, Order.BID, amount, limit, entity=self)
        else:
            logger.debug("placing ask order")
            oid = self.private.ask(amount, limit)
            return BitfinexOrder(oid, self.market, now, Order.ASK, amount, limit, entity=self)

    def cancelOrder(self, order):
        """Cancel an existing order"""
        assert(isinstance(order, BitfinexOrder))

        logger.debug("cancelling order {0}".format(order.oid))

        oid = order.oid
        if order.is_bid_order():
            result = self.private.cancel_bid(oid)
        else:
            result = self.private.cancel_ask(oid)

        if not result:
            raise ActiveParticipant.ActiveParticipantError()

    def getOpenOrders(self):
        """Gets all the open orders"""

        logger.debug("getting open orders")

        low_level_orders = self.private.orders()
        orders = []

        for o in low_level_orders:
            currency = Currency(o['currency'])
            oid = o['oid']
            timestamp = datetime.fromtimestamp(o['date'])
            order_type = Order.BID if o['type'] else Order.ASK
            amount = Amount(Decimal(o['amount']['value_int']) / self.market._multiplier(BTC), BTC)
            price = self.market.xchg_factory( Decimal(o['price']['value_int']) / self.market._multiplier(currency))
            order = BitfinexOrder( oid, self.market, timestamp, order_type, amount, price, entity=self)

            # add additional status from Bitfinex
            order.status = o['status']

            orders.append(order)

        return orders

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<BitfinexParticipant({0})>".format(self.market.currency1)
