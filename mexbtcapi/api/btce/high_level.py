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
from mexbtcapi.concepts.market import ActiveParticipant, Market as BaseMarket, Order, Trade, SecretContainer

from public import getDepth, getTradeHistory
from trade import TradeAPI
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
            .format(self.market, self.timestamp, self.oid, self.order_type,
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

class BTCeSimpleSecretContainer(SecretContainer):
    """
    Simply contains the secret, key and nonce.
    """
    def __init__(self, secret, key, nonce):
        self.secret = secret
        self.key = key
        self.nonce = nonce

class BTCeSecretFileContainer(SecretContainer):
    """
    Keeps the secret in a file, saving the nonce information when done.
    """
    def __init__(self, filename, key, participant):
        # Note that the participant must also be a singleton for a specific key
        from keyhandler import KeyHandler
        self.key_handler = KeyHandler(filename)
        self.key = key
        self.participant = participant
        self.filename = filename

    @property
    def secret(self):
        return self.key_handler.keys[self.key][0]

    @property
    def nonce(self):
        return self.key_handler.keys[self.key][1]

    def __del__(self):
        n = self.participant.private.next_nonce() + 1
        self.key_handler.setNextNonce(self.key, n)
        self.key_handler.save(self.filename)

class BTCeParticipant(ActiveParticipant):
    def __init__(self, market, secret_info = None):
        super(BTCeParticipant, self).__init__(market)
        self.private = None
        if secret_info:
            self.setPrivate(secret_info)

    def setPrivate(self, secret_info):
        self.private = TradeAPI(secret_info.key, secret_info.secret, secret_info.nonce)

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
            price = 0.1 if order.is_sell_market_order() else 399.99
            assert order.order_type in [Order.MARKET_SELL, Order.MARKET_BUY]

            limit = ExchangeRate(self.market.currency2, self.market.currency1, price)
        
        if order.from_amount.currency == market.currency1:
            amount = limit.convert(order.from_amount)
        elif order.from_amount.currency == market.currency2:
            amount = order.from_amount
        else:
            assert False
        print amount
        raw_input()

        info = self.private.trade(market.currency_pair, typ, limit.convert(Amount(1, market.currency2)).value, amount.value)
        
        return self._makeReturnOrder(info, typ, limit)

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
        
        try:
            low_level_orders = self.private.orderList(pair = self.market.currency_pair, active = True)
        except Exception, e:
            if 'no orders' in str(e):
                return []
            else: raise

        orders = []

        for o in low_level_orders:
            currency = self.market.currency1
            oid = o.order_id
            timestamp = o.timestamp_created
            order_type = Order.BID if o.type == 'buy' else Order.ASK
            amount = Amount(Decimal(o.amount), self.market.currency2)
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
