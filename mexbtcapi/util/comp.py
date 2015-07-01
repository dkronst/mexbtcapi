#!/usr/bin/env python

from mexbtcapi.concepts.currency import ExchangeRate, Amount

class Compare(object):
    def __init__(self, reverse, currency):
        if reverse:
            self.reverse = -1
        else:
            self.reverse = 1

        self.currency = currency

    def __call__(self, x, y):
        return self.reverse*self._cmp(x, y)
        
    def _cmp(self, x, y):
        a = x.exchange_rate.convert(Amount(1, self.currency)).value > y.exchange_rate.convert(Amount(1, self.currency)).value
        if a > 0:
            return 1
        elif a == 0:
            return 0
        else:
            return -1

def comp(c):
    return Compare(False, c)

def dcomp(c):
    return Compare(True, c)
