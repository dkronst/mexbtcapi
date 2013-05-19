#!/usr/bin/env python

"""
Implements the High-level API for btc-e so that it can be used 
with the mexbtcapi package
"""

from datetime import datetime, timedelta
from decimal import Decimal
import logging

from mexbtcapi import concepts
from mexbtcapi.concepts.currencies import *
from mexbtcapi.concepts.currency import Amount, Currency, ExchangeRate
from mexbtcapi.concepts.market import ActiveParticipant, Market as BaseMarket, Order, Trade

from public import getDepth, getTradeHistory
rom trade import TradeAPI
from scraping import scrapeMainPage
from keyhandler import KeyHandler

logger = logging.getLogger(__name__)


class BTCeTicker(concepts.market.Ticker):
    TIME_PERIOD = timedelta(days=1)

    def __repr__(self):
        return \
            "<BTCeTicker({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8})" \
            .format(self.market, self.time, self.high, self.high, self.last,
            self.volume, self.average, self.buy, self.sell)


class BTCeOrder(Order):

    def __init__(self, oid, *args, **kwargs):
        super(BTCeOrder, self).__init__(*args, **kwargs)
        self.oid = oid

    def __repr__(self):
        return \
            "<BTCeOrder({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}>" \
            .format(self.market, self.timestamp, self.oid, self.buy_or_sell,
            self.from_amount, self.exchange_rate, self.properties, self.entity)


class BTCeMarket(BaseMarket):
    MARKET_NAME = "BTCe"

    def __init__(self, currency, item = BTC):
        super(BTCeMarket, self).__init__(self.MARKET_NAME, currency, item)
        self.currency_pair = self._getCurrencyPair()

    def getTicker(self):
        logger.debug("getting ticker")

        raise NotImplementedError()

        time = datetime.now()
        data = (self.currency1.name)

        data2 = [Decimal(data[name]['value_int']) /
                 self._multiplier(self.currency1)
                 for name in ('high', 'low', 'avg', 'last', 'sell', 'buy')]
        high, low, avg, last, sell, buy = map(self.xchg_factory, data2)

        volume = Decimal(data['vol']['value_int']) / self._multiplier(BTC)
        ticker = BTCeTicker(market=self, time=time, high=high, low=low,
                             average=avg, last=last, sell=sell, buy=buy,
                             volume=volume)
        return ticker

    def _getCurrencyPair(self):
        return "%s_%s"%(self.currency2.name.lower(), self.currency1.name.lower())

    def getDepth(self):
        logger.debug("getting depth")
        
        asks, bids = getDepth(self._getCurrencyPair())

        ret = {
            'asks': self._depthToOrders(asks, Order.ASK),
            'bids': self._depthToOrders(bids, Order.BID),
        }
        return ret

    def _depthToOrders(self, depth, order_type):
        orders = []
        timestamp = datetime.now() # Don't need the information about each order when checking depth

        for p, v in depth:
            # TODO: change the low-level stream to use Amount instead of numbers
            # this means also changing the "hash" of Amount.
            amount = Amount(Decimal(v), self.currency2)
            price = ExchangeRate(self.currency2, self.currency1, Decimal(p))
            order = Order(self, timestamp, order_type, amount, price)
            orders.append(order)

        return orders


class BTCeParticipant(ActiveParticipant):
    def __init__(self, market, secret_info = None, key_handler = None):
        super(BTCeParticipant, self).__init__(market)
        assert secret_info and key_handler
        self.key_handler = key_handler
        if secret_info:
            self.private = trade.TradeAPI(secret_info.key, secret_info.secret, secret_info.nonce)
        elif key_handler:
            self.private = self._getTradeApiFromHandler(key_handler)
        else:
            raise Exception("Must supply either secret_info or key_handler")

    def _makeReturnOrder(self, info, typ, exchange):
        a = Amount(info.remains, self.market.currency1)
        return BTCeOrder(info.order_id, self.market, datetime.now(), typ, a, exchange, entity = self)

    def placeOrder(self, order):
        """places an Order in the market for limit/amount"""
        now = datetime.now()
        market = self.market
        typ = ((order.is_bid_order() or order.is_buy_market_order()) and "buy") or "sell"
        logger.debug("placing %s order"%typ)

        limit = order.exchange_rate
        if not limit:
            price = 0.00001 if order.is_sell_market_order() else 99999.99
            assert order.order_type in [Order.MARKET_SELL, Order.MARKET_BUY]

            limit = ExchangeRate(self.market.currency2, self.market.currency1, price)

        info = self.private.trade(market.currency_pair, typ, limit.convert(Amount(1, market.currency1)), order.from_amount.value)
        
        return self._makeReturnOrder(info)

    def cancelOrder(self, order):
        """Cancel an existing order"""
        raise NotImplementedError()
        assert(isinstance(order, BTCeOrder))

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

        low_level_orders = self.private.orderList(pair = self.market.currency_pair, active = True)
        orders = []

        for o in low_level_orders:
            currency = self.market.currency1
            oid = o.order_id
            timestamp = o.timestamp_created
            order_type = Order.BID if o.type == 'buy' else Order.ASK
            amount = Amount(Decimal(o.amount), self.currency2)
            price = ExchangeRate(self.market.currency2, self.market.currency1, Decimal(o.rate))
            order = BTCeOrder( oid, self.market, timestamp, order_type, amount, price, entity=self)

            # add additional status from BTCe
            order.status = o.status
            orders.append(order)

        return orders

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<BTCeParticipant({0})>".format(self.market.currency1)
