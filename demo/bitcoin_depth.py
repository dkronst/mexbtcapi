import mexbtcapi
from mexbtcapi.concepts.currencies import USD,BTC
from mexbtcapi.concepts.currency import Amount

import matplotlib.pyplot as plt


dollars= "100"*USD
for api in mexbtcapi.apis:
#    try:
        depth = api.market(USD).getDepth()
        x = [o.from_amount.value for o in depth['asks']]
        y = [float(o.exchange_rate.convert(Amount(1, BTC)).value) for o in depth['asks']]
        print y
        plt.plot(x, y)
        plt.show()
#    except Exception, e:
#        print "Failed to use "+api.name 
