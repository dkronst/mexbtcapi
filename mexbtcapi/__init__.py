from api import bitstamp
from api import btce
from api import vircurex
from api import bitfinex
import logging

logging.basicConfig()
logging.getLogger(__name__)

apis = [btce,
	bitstamp,
        vircurex,
        bitfinex,
		]
