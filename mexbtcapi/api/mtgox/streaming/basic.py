#!/usr/bin/env python
import json
from Queue import Queue

try:
    import websocket
except ImportError as e:
    raise ImportError("You need to install the websocket module. \
        Get it from https://github.com/liris/websocket-client.git")

import threading

CHANNEL_IDS = {"depth":"24e67e0d-1cad-4cc0-9e7a-f8523ef460fe",
               "ticker":"d5f06780-30a8-4a48-a2f8-7ed181b4a13f",
               "trade":"dbf1dee9-4f2e-4a08-8cb7-748919a71b21"}


class MtGoxStream(object):
    """
    Represent a single MtGox stream
    """
    class CommThread(threading.Thread):
        """
        Implements a thread which listens to subscriptions on the given channels
        """
        def __init__(self, stream):
            threading.Thread.__init__(self)
            self.stream = stream
            self.ws = stream.ws

            # The idea here is to use queues as a message passing mechanism
            # to prevent all those ugly synchronization problems
            self.to_send = Queue()
            self.to_recv = Queue()
            self.valid = True
            self.setDaemon(True) # Don't hang the process when interrupted

        def processMessage(self, msg):
            """
            Process message given by msg and routes it to the correct
            channel
            """
            op = msg.get('op', 'n/a')
            if op == 'subscribe':
                # The following will happen when someone subscribes
                # The subscribing thread will have to wait until the
                # subscription is given before adding another one
                # See implementation following
                to_recv.put_nowait(msg['channel'])
                return
            elif op == 'private':
                for ch in self.stream.channels:
                    if ch.ch_id == msg['channel']:
                        print "push", ch.ch_id, ch.ch_type 
                        ch.push_msg(msg)
            elif op == 'remark':
                self.stream.remarks.put_nowait(msg)
            else:
                pass # TODO: handle unsubscribe


        def run(self):
            """
            Main thread loop
            """

            while self.valid:
                while not self.to_send.empty():
                    s = json.dumps(self.to_send.get())
                    print "sending %r"%s
                    self.ws.send(s)
                
                msg = self.stream.ws.recv()
                self.processMessage(json.loads(msg))

    def __init__(self, currencies):
        """
        Initialize a MtGox stream...
        currencies - A list of Currency objects for this stream
        """
        self.currencies = currencies
        self.ws = websocket.WebSocket()
        self.ws.connect('wss://websocket.mtgox.com/mtgox?Currency=USD') # TODO: Verify cert
        self.sock = self.ws.sock
        self.subscriptions = {}
        self.channels = []
        self.remarks = Queue()
        self.startCommThread()

    def startCommThread(self):
        """
        Start the communication thread after connecting
        """
        self.comm_thread = self.CommThread(self)
        self.comm_thread.start()

    def subscribe(self, channel):
        """
        Subscribe this stream to a channel
        channel is a MtGoxChannel object
        """
        if channel.ch_type not in CHANNEL_IDS:
            d = {"op":"mtgox.subscribe", "type":channel.ch_type}
            self.comm_thread.to_send.put_nowait(d)
            res = self.comm_thread.to_recv.get()
            assert('channel' in res)
            assert('op' in res and res['op'] == 'subscribe')
            channel.ch_id = res['channel']
            #logging.info("Subscribed to channel %s for %s"%(d['type'], res['channel'])
            print "Subscribed to channel %s for %s"%(d['type'], res['channel'])
        else:
            print "Subscribed to a constant channel: %r"%channel.ch_id
        self.channels.append(channel)
        

    def unsubscribe(self, channel):
        """
        unsubscribe from a specific channel
        """

    def __del__(self):
        self.ws.close()
        self.comm_thread.valid = False

class MtGoxChannel(object):
    """
    Represents a MtGox channel which you can subscribe to, such as a depth channel
    """
    def __init__(self, ch_type):
        """
        Initialize the Channel object
        ch_type - a string, can be one of ['ticker', 'trade', 'depth']
        """
        self.msg_queue = Queue()
        self.ch_type = ch_type
        self.msg_event = threading.Event()

    def push_msg(self, msg):
        """
        Push a message to the message queue
        """
        self.msg_queue.put_nowait(msg)
        self.msg_event.set()
    
class NoSubscriptionChannel(MtGoxChannel):
    """
    Several of the channels that MtGox has don't require subscription and
    being broadcast constantly. This class represents such a channel
    """
    def __init__(self, ch_type):
        MtGoxChannel.__init__(self, ch_type)
        self.ch_id = CHANNEL_IDS[ch_type]

class DepthChannel(NoSubscriptionChannel):
    """
    Represents a market depth channel. Every time a message
    is given, it's put on a queue. When the depth is queried 
    the queue is emptied by adding all the messages together
    """
    def __init__(self, initial_depth):
        """
        Constructs this depth channel. 
        initial_depth is the dictionary given from the http API and we will
        build on that.
        """
        NoSubscriptionChannel.__init__(self, "depth")
        self.depth_info = initial_depth.copy()

    def _add_to_depth(self, msg):
        """
        Adds a message to current depth
        """
        dpt = msg["depth"]
        price_int = int(dpt['price_int'])
        volume_int = int(dpt['volume_int'])
        typ = dpt['type_str']
        self.depth_info[typ][price_int] = self.depth_info[typ].get(price_int, 0) + price_int
        if self.depth_info[typ][price_int] == 0:
            del self.depth_info[typ][price_int]

    def depth(self):
        """
        Returns the current depth as given by this channel
        The returned depth_info should be copied if changes are to be made to it.
        """
        while not self.msg_queue.empty():
            self._add_to_depth(self.msg_queue.get())
        return self.depth_info

    def simulate_buy(self, amount):
        """
        Tries to simulate a buy order
        Returns the number of items that can be bought with amount
        """
        # TODO: Finish implmeneting this
        raise NotImplementedError

    def simulate_sell(self, amount):
        """
        Same as simulate_buy only for sell
        """
        # TODO: Finish implementing this
        raise NotImplementedError

class TradeChannel(NoSubscriptionChannel):
    # Not implemented properly yet
    """
    Represent the Trade Channel of MtGox. Messages are put on a queue
    and an event is set when a new trade is given.
    """
    def __init__(self):
        """
        Constructs this depth channel. 
        initial_depth is the dictionary given from the http API and we will
        build on that.
        """
        NoSubscriptionChannel.__init__(self, "trade")

    def readTrade(self):
        """
        TODO: fix to give the proper data structure
        """
        return self.msg_queue.get()


if __name__=='__main__':
    gox = MtGoxStream(None)
    print "stream created"
    d = DepthChannel({"ask":{1:10}, "bid":{1:10}})
    t = TradeChannel()

    print "sucscribing"
    gox.subscribe(t)
    gox.subscribe(d)
    print "done..."
    import time
    time.sleep(10)
    print d.depth()

