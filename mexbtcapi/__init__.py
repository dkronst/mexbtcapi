from api import mtgox
from api import bitcoin24
from api import bitstamp
from api import btce
from api import vircurex
import logging

logging.basicConfig()
logging.getLogger(__name__)

apis = [mtgox,
#		bitcoin24,   # No longer operational
        btce,
		bitstamp,
        vircurex
		]
