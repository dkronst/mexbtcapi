from api import bitstamp
from api import btce
import logging

logging.basicConfig()
logging.getLogger(__name__)

apis = [btce,
		bitstamp,
		]
