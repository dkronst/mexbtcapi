from currency import ExchangeRate, Amount
from datetime import datetime, timedelta
from decimal import Decimal

from mexbtcapi.util.comp import comp, dcomp


class Trade(object):
    """Represents an exchange of two currency amounts.
    May include the entities between which the trade is made
    """

    def __init__(self, market, timestamp, from_amount, exchange_rate):
        assert isinstance(market, Market)  # must not be null
        assert isinstance(timestamp, datetime)  # must not be null
        assert isinstance(from_amount, Amount)
        assert isinstance(exchange_rate, ExchangeRate)

        self.market = market
        self.timestamp = timestamp
        self.from_amount = from_amount
        self.exchange_rate = exchange_rate

    @property
    def to_amount(self):
        return self.exchange_rate.convert(self.from_amount)

    def __str__(self):
        return "{0} -> {1}".format(self.from_amount, self.exchange_rate)

    def __repr__(self):
        return "<Trade({0}, {1}, {2}, {3}>".format(self.market, self.timestamp,
                    self.from_amount, self.exchange_rate)


class Order(object):
    """Represents an order to buy or sell a number of from_amount for
    exchange_rate.

    For now, more specific properties can be set through the properties
    parameter of the constructor.
    """

    BID = 'BID'
    ASK = 'ASK'
    MARKET_BUY = 'MARKET_BUY'
    MARKET_SELL = 'MARKET_SELL'

    def __init__(self, market, timestamp, order_type, from_amount,
                 exchange_rate, properties="", entity=None):
        assert isinstance(market, Market)  # must not be null
        assert timestamp is None or isinstance(timestamp, datetime) # None means now
        assert order_type in [self.BID, self.ASK, self.MARKET_BUY, self.MARKET_SELL]
        assert isinstance(from_amount, Amount)
        assert not (order_type in [self.BID, self.ASK]) or isinstance(exchange_rate, ExchangeRate)
        assert isinstance(properties, str)
        assert entity is None or isinstance(entity, Participant)

        self.market = market
        self.timestamp = timestamp or datetime.now()
        self.order_type = order_type
        self.from_amount = from_amount
        self.exchange_rate = exchange_rate # or limit in case of ask/bid orders
        self.properties = properties
        self.entity = entity
    
    def expense(self):
        """
        Returns the maximum expense needed to complete this transaction - i.e. the 
        amount exchanged at the exchange rate
        """
        return self.exchange_rate.convert(self.from_amount)

    def is_bid_order(self):
        return self.order_type == self.BID

    def is_ask_order(self):
        return self.order_type == self.ASK

    def is_buy_market_order(self):
        return self.order_type == self.MARKET_BUY

    def is_sell_market_order(self):
        return self.order_type == self.MARKET_SELL

    def __str__(self):
        return "{0} -> {1}".format(self.from_amount, self.exchange_rate)

    def __repr__(self):
        return "<Order({0}, {1}, {2}, {3}>".format(self.market, self.timestamp,
                    self.from_amount, self.exchange_rate)


class Market(object):
    """Represents a market - where Trades are made
    """
    class InvalidOrder(Exception):
        '''raised when there's something wrong with an order, in this
        market's context'''

    def __init__(self, market_name, buy_currency, sell_currency):
        """
        Currency1 is the "buy" currency, i.e. the currency used to 
        buy the "sell_currency" or in other words the 'item' sold
        on this exchange
        """
        self.name = market_name
        self.currency1 = buy_currency
        self.currency2 = sell_currency

    def getTicker(self):
        """Returns the most recent ticker"""
        raise NotImplementedError()

    def getDepth(self):
        """
        Returns the depth book as a dictionary with two keys: 'asks', 'bids'. Each containing 
        a list of orders representing each
        """
        raise NotImplementedError()

    def simulateOrder(self, order):
        """
        Simulates an order if given right now. Returns a tupple of the currency used
        and the item. The currency is the currency left after this order (left over from this
        order only!) and the item is how much of the item will be gained if this
        order was placed right now (actual results may vary due to engine lag)

        returns a tupple of amounts with currency and the item respectively
        """
        def upperLimit(d, order):
            a = Amount(1, self.currency2)
            return d.exchange_rate.convert(a) > order.exchange_rate.convert(a)
        def lowerLimit(d, order):
            a = Amount(1, self.currency2)
            return d.exchange_rate.convert(a) < order.exchange_rate.convert(a)

        # this is a fairly generic implementation. It should work for
        # all markets that implement "getDepth" properly

        depth = self.getDepth()
        # There are 4 possibilities for bid/ask orders:
        # 1. bid is given in C1 => e.g. buy 100 USD of BTC limit 150 => take 100 USD and spend them until limit is reached
        # 2. bid is given in C2 => e.g. buy 1 BTC, limit 150 => buy AT MOST 1 BTC with - spend USD until 1 BTC is reached or limit
        # 3. ask is given in C1 => e.g. sell 100 USD worth of BTC => sell BTC until you reach limit or 100 dollars
        # 4. ask is given in C2 => e.g. sell 1 BTC with limit => sell until 1 BTC is reached or limit
        #
        # So there are 2 factors: the amount to sell/buy and the limit. 
        # Selling BTC is the same as buying USD so we can use that - but in that case the limit still has to be
        # used. 

        if order.order_type in [Order.BID, Order.MARKET_BUY]:
            # e.g. Selling amount is given in USD but selling BTC
            limit = upperLimit
        else:
            limit = lowerLimit

        if order.order_type == Order.MARKET_BUY:
            order.exchange_rate = ExchangeRate(self.currency2, self.currency1, '9999999')
        if order.order_type == Order.MARKET_SELL:
            order.exchange_rate = ExchangeRate(self.currency2, self.currency1, '0.001')

        sim_c = (order.from_amount.currency == self.currency1 and self.currency2) or self.currency1

        bucket = order.from_amount.clone() # starting with a full amount of currency and subtracting as we go...

        # If we are buying we need to look at the sorted asks, and vice versa
        dp = (order.order_type in [Order.BID, Order.MARKET_BUY] and sorted(depth['asks'], comp(self.currency2)) \
                or sorted(depth['bids'], dcomp(self.currency2)))
        total_transacted = Amount(0, sim_c)

        for d in dp:
            next_chunk = d.exchange_rate.convert(d.from_amount, order.from_amount.currency)
            if limit(d, order):
                break
            if next_chunk > bucket: # We don't have enough in the bucket to complete this chunk
                # The limit was not reached at this depth...
                total_transacted += d.exchange_rate.convert(bucket, sim_c)
                bucket = Amount(0, order.from_amount.currency)
                break
            total_transacted += d.exchange_rate.convert(next_chunk, sim_c)
            bucket -= next_chunk
        return total_transacted, order.from_amount - bucket



    def getTrades(self):
        """Returns all completed trades"""
        raise NotImplementedError()

    def _orderSanityCheck(self, order):
        '''checks if an order is adequate in this market'''
        er= order.exchange_rate
        if order.market and order.market!=self:
            raise self.InvalidOrder("Order on different market")
        try:
            assert er.otherCurrency( self.currency1) == self.currency2
        except AssertionError, ExchangeRate.BadCurrency:
            raise self.InvalidOrder("Invalid order exchange rate")

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Market({0}, {1}, {2})>".format(self.name,
                    self.currency1, self.currency2)


class Participant(object):
    """Represents a participant in a market
    """

    def __init__(self, market):
        assert isinstance(market, Market)
        self.market = market


class PassiveParticipant(Participant):
    """A participant over which the user has no control
    """

    pass


class ActiveParticipant(Participant):
    """A participant under user control (may be the user itself)
    """
    class ActiveParitipantError(Exception):
        """Base ActiveParticipant error"""
        pass

    class OrderAlreadyClosedError(ActiveParitipantError):
        """Occurs when trying to cancel a already-closed Order"""
        pass

    class NotAuthorizedError(ActiveParitipantError):
        """Occurs when the user is not authorized to do the requested operation
        """
        pass

    def placeOrder(self, order):
        """places an Order in the market"""
        raise NotImplementedError()

    def cancelOrder(self, order):
        """Cancel an existing order"""
        raise NotImplementedError()

    def getOpenOrders(self):
        """Gets all the open orders"""
        raise NotImplementedError()


class Ticker(object):
    """Ticker datapoint
    """

    # time period (in seconds) associated with the
    # returned results: high, low, average,
    # last, sell, buy, volume
    TIME_PERIOD = timedelta(days=1)
    RATE_FIELDS= ('high', 'low', 'average', 'last', 'sell', 'buy')

    def __init__(self, market, time, high=None, low=None, average=None,
                    last=None, sell=None, buy=None, volume=None):
        """
        market: the market this ticker is associated with
        time:   the time at which this ticker was retrieved. This is preferably
                the server time, if available.
        high, low, average, last, sell, buy: ExchangeRate.
        """
        assert isinstance(market, Market)
        assert all([x is None or isinstance(x, ExchangeRate) 
            for x in map(locals().__getitem__,self.RATE_FIELDS)])
        assert (volume is None) or (type(volume) == long) or (type(volume) == Decimal)
        assert (buy is None and sell is None) or (buy <= sell)
        assert isinstance(time, datetime)
        self.market, self.time, self.volume = market, time, volume
        self.high, self.low, self.average, self.last, self.sell, self.buy = \
            high, low, average, last, sell, buy

    def __repr__(self):
        return \
            "<Ticker({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8})" \
            .format(self.market, self.time, self.high, self.high, self.last,
            self.volume, self.average, self.buy, self.sell)
