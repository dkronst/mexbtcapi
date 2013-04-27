from datetime import datetime, timedelta
from decimal import Decimal
from functools import partial
import logging

from mexbtcapi import concepts
from mexbtcapi.concepts.currencies import BTC
from mexbtcapi.concepts.currency import Amount, Currency, ExchangeRate
from mexbtcapi.concepts.market import ActiveParticipant, Market as BaseMarket, Order, Trade
import mtgox as low_level
from mexbtcapi.api.mtgox.streaming import basic as streamapi


logger = logging.getLogger(__name__)


class MtGoxTicker(concepts.market.Ticker):
    TIME_PERIOD = timedelta(days=1)

    def __repr__(self):
        return \
            "<MtGoxTicker({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8})" \
            .format(self.market, self.time, self.high, self.high, self.last,
            self.volume, self.average, self.buy, self.sell)


class MtGoxOrder(Order):

    def __init__(self, oid, *args, **kwargs):
        super(MtGoxOrder, self).__init__(*args, **kwargs)
        self.oid = oid

    def __repr__(self):
        return \
            "<MtGoxOrder({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}>" \
            .format(self.market, self.timestamp, self.oid, self.buy_or_sell,
            self.from_amount, self.exchange_rate, self.properties, self.entity)


class MtGoxMarket(BaseMarket):
    MARKET_NAME = "MtGox"

    def __init__(self, currency, item = BTC):
        super(MtGoxMarket, self).__init__(self.MARKET_NAME, currency, item)

        # to convert low level data
        self.multiplier = low_level.multiplier
        self.xchg_factory = partial(concepts.currency.ExchangeRate,
                                    BTC, currency)
        self.mtgox_stream = None

    def _multiplier(self, currency):
        return self.multiplier[currency.name]

    def getTicker(self):
        logger.debug("getting ticker")

        time = datetime.now()
        data = low_level.ticker(self.currency1.name)

        data2 = [Decimal(data[name]['value_int']) /
                 self._multiplier(self.currency1)
                 for name in ('high', 'low', 'avg', 'last', 'sell', 'buy')]
        high, low, avg, last, sell, buy = map(self.xchg_factory, data2)

        volume = Decimal(data['vol']['value_int']) / self._multiplier(BTC)
        ticker = MtGoxTicker(market=self, time=time, high=high, low=low,
                             average=avg, last=last, sell=sell, buy=buy,
                             volume=volume)
        return ticker

    def getDepth(self):
        logger.debug("getting depth")
        if not self.mtgox_stream:
            self.mtgox_stream = streamapi.MtGoxStream(None)
            low_level_depth = low_level.depth()
            self.depth_channel = streamapi.DepthChannel(low_level_depth)
        
        low_level_depth = self.depth_channel.depth()

        ret = {
            'asks': self._depthToOrders(low_level_depth['asks'], Order.ASK),
            'bids': self._depthToOrders(low_level_depth['bids'], Order.BID),
        }
        return ret

    def _depthToOrders(self, depth, order_type):
        orders = []

        for d in depth:
            # TODO: change the low-level stream to use Amount instead of numbers
            # this means also changing the "hash" of Amount.
            timestamp = datetime.now() # Don't need the information about each order when checking depth
            amount = Amount(Decimal(depth[d]) / Decimal(self._multiplier(BTC)), BTC)
            price = self.xchg_factory(Decimal(d) / Decimal(self._multiplier(self.currency1)))
            order = Order(self, timestamp, order_type, amount, price)
            orders.append(order)

        return orders

    def simulateOrder(self, order):
        """
        Simulates putting the given order on the market RIGHT NOW (engine lag may change 
        the result if actually placed). 
        returns a tupple of amounts with currency and item respectively
        """
        cmp = lambda x,y: int(float(x.exchange_rate.convert(Amount(1, BTC)).value - 
            y.exchange_rate.convert(Amount(1, BTC)).value)*10E+6)
        dcmp = lambda x,y: -cmp(x,y)

        depth = self.getDepth()

        # TODO: Implement the rest...

        if order.is_bid_order():
            total_item = Amount(0, self.currency2)
            currency_left = order.from_amount
            sorted_depth = sorted(depth['bids'], dcmp)
            while sorted_depth and currency_left:
                od = sorted_depth.pop()
                currency_chunk = od.expense()
                if currency_left > od.expense():
                    currency_left -= currency_chunk
                    total_item += od.exchange_rate.convert(currency_chunk)
                else:
                    total_item += od.exchange_rate.convert(currency_left)
                    currency_left = 0.0

        return currency_left, total_item

    def getTrades(self):
        logger.debug("getting trades")

        low_level_trades = low_level.trades()

        # convert tradres to array of Trades
        trades = []
        for trade in low_level_trades:
            price = Decimal(trade['price_int']) / \
                self._multiplier(self.currency1)
            amount = Decimal(trade['amount_int']) / \
                self._multiplier(BTC)
            timestamp = datetime.fromtimestamp(trade['date'])

            btc_amount = Amount(amount, BTC)
            exchange_rate = self.xchg_factory(price)

            t = Trade(self, timestamp, btc_amount, exchange_rate)
            t.tid = ['tid']

            trades.append(t)

        return trades


class MtGoxParticipant(ActiveParticipant):

    def __init__(self, market, key, secret):
        super(MtGoxParticipant, self).__init__(market)
        self.private = low_level.Private(key, secret)

    def placeOrder(self, order):
        """places an Order in the market for limit/amount"""
        now = datetime.now()
        if order.is_bid_order():
            logger.debug("placing bid order")
            oid = self.private.bid(order.from_amount.value, order.exchange_rate)
            return MtGoxOrder(oid, self.market, now, Order.BID, amount, limit, entity=self)
        else:
            logger.debug("placing ask order")
            oid = self.private.ask(amount, limit)
            return MtGoxOrder(oid, self.market, now, Order.ASK, amount, limit, entity=self)

    def cancelOrder(self, order):
        """Cancel an existing order"""
        assert(isinstance(order, MtGoxOrder))

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
            order = MtGoxOrder( oid, self.market, timestamp, order_type, amount, price, entity=self)

            # add additional status from MtGox
            order.status = o['status']

            orders.append(order)

        return orders

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<MtGoxParticipant({0})>".format(self.market.currency1)
