# -*- coding: utf-8 -*-

# Copyright © 2012 Petter Reinholdtsen <pere@hungry.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from decimal import Decimal
from functools import partial
import datetime

import mexbtcapi
from mexbtcapi import concepts
from mexbtcapi.concepts.currencies import BTC, USD
from mexbtcapi.concepts.currency import Amount, ExchangeRate
from mexbtcapi.concepts.market import Market as BaseMarket, PassiveParticipant, Order

import urllib
import urllib2
import sys
import json

try:
    from bitstamp import client
except ImportError:
    print "Couldn't find module bitstamp. Download and install from:"
    print "https://github.com/kmadac/bitstamp-python-client.git"
    sys.exit(1)

MARKET_NAME= "Bitstamp"
_URL = "https://www.bitstamp.net/api/"

class BitStampTicker( concepts.market.Ticker):
    TIME_PERIOD= 24*60*60

class BitstampMarket(BaseMarket):
    def __init__( self, currency, currency2 = BTC):
        mexbtcapi.concepts.market.Market.__init__(self, MARKET_NAME, currency, BTC)
        if currency != USD:
            raise Exception("Currency not supported on Bitstamp: " + currency)
        self.xchg_factory = partial(ExchangeRate, BTC, USD)
        self.public_api = client.public()

    def getTicker(self):
        url = _URL + "ticker"
        data = self.public_api.ticker()
        for x,y in [('bid','buy'),('ask','sell')]:
            data[y]= data[x]
        fields= list(BitStampTicker.RATE_FIELDS)
        fields.remove('average') #not present on Bitstamp API
        data2 = dict( [ (x, self.xchg_factory(data[x])) for x in fields] )
        data2['time']= datetime.datetime.now()
        return BitStampTicker( market=self, **data2 ) 

    def getDepth(self):
        data = self.public_api.order_book()
        #print data
        ret = {}
        for typ in ('bids', 'asks'):
            depth = []
            ret[typ]=depth
            for o in data[typ]:
                rate = Decimal(o[0])
                amount = Decimal(o[1])
                from_amount = Amount(rate * amount, USD)
                price = self.xchg_factory(rate)
                order_type = (typ == 'bids' and Order.BID) or Order.ASK
                depth.append(Order(self, None, order_type, from_amount, price))
        return ret

