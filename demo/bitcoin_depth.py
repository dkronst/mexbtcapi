import mexbtcapi
from mexbtcapi.concepts.currencies import USD,BTC
from mexbtcapi.concepts.currency import Amount


import matplotlib.pyplot as plt

from decimal import Decimal

for api in mexbtcapi.apis:
#    try:
        from mexbtcapi.util.comp import comp, dcomp
        depth = api.market(USD).getDepth()
        for typ in ['asks', 'bids']:
            keys = sorted(depth[typ], comp(BTC) if typ=='asks' else dcomp(BTC))
            keys = [k for k in keys if k.exchange_rate.convert(Amount(Decimal(1.0), BTC)).value < 500] # This is arbitrary. Best is to use max/min values.
            v = 0.0
            y = []

            for vol in (float(o.from_amount.value) for o in keys):
                v += vol
                y.append(v)

            x = [float(o.exchange_rate.convert(Amount(Decimal(1.0), BTC)).value) for o in keys]

            if typ == 'asks':
                plt.plot(x, y, 'b')
            else:
                plt.plot(x, y, 'r')
        plt.show()
#    except Exception, e:
        print "Failed to use "+api.name
        raise
