from public import getDepth, getTradeHistory
from trade import TradeAPI
from scraping import scrapeMainPage
from keyhandler import KeyHandler

import mexbtcapi.api.btce

from mexbtcapi.api.btce.high_level import BTCeMarket, BTCeParticipant
import logging

logging.getLogger(__name__)

name = BTCeMarket.MARKET_NAME
market = BTCeMarket
participant = BTCeParticipant
