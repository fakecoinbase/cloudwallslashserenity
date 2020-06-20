import asyncio
import json
import logging
from typing import List

import fire
import websockets
from phemex import PhemexConnection
from tau.core import MutableSignal, NetworkScheduler, Event, Signal
from tau.signal import Filter, FlatMap, Map

from serenity.db import InstrumentCache
from serenity.marketdata.fh.feedhandler import FeedHandlerState, WebsocketFeedHandler, ws_fh_main, Feed, \
    OrderBookBuilder
from serenity.marketdata import Trade, OrderBookEvent, OrderBookSnapshot, OrderBookUpdate, BookLevel
from serenity.model.exchange import ExchangeInstrument


class PhemexFeedHandler(WebsocketFeedHandler):

    logger = logging.getLogger(__name__)

    def __init__(self, scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id: str = 'prod'):
        if instance_id == 'prod':
            self.ws_uri = 'wss://phemex.com/ws'
            self.phemex = PhemexConnection()
        elif instance_id == 'test':
            self.ws_uri = 'wss://testnet.phemex.com/ws'
            self.phemex = PhemexConnection(api_url='https://testnet-api.phemex.com')
        else:
            raise ValueError(f'Unknown instance_id: {instance_id}')

        # ensure we've initialized PhemexConnection before loading instruments in super()
        super().__init__(scheduler, instrument_cache, instance_id)

        self.instrument_trades = {}
        self.instrument_order_book_events = {}
        self.instrument_order_books = {}

    @staticmethod
    def get_uri_scheme() -> str:
        return 'phemex'

    def _load_instruments(self):
        self.logger.info("Downloading supported products")
        products = self.phemex.get_products()
        for product in products['data']:
            symbol = product['symbol']
            base_ccy = product['baseCurrency']
            quote_ccy = product['quoteCurrency']
            price_scale = product['priceScale']

            ccy_pair = self.instrument_cache.get_or_create_currency_pair(base_ccy, quote_ccy)
            instr = ccy_pair.get_instrument()
            exch_instrument = self.instrument_cache.get_or_create_exchange_instrument(symbol, instr, "Phemex")
            self.logger.info(f'\t{symbol} - {base_ccy}/{quote_ccy} [ID #{instr.get_instrument_id()}]')
            self.known_instrument_ids[symbol] = exch_instrument
            self.instruments.append(exch_instrument)
            self.price_scaling[symbol] = price_scale

    def _create_feed(self, instrument: ExchangeInstrument):
        symbol = instrument.get_exchange_instrument_code()
        return Feed(instrument, self.instrument_trades[symbol], self.instrument_order_book_events[symbol],
                    self.instrument_order_books[symbol])

    # noinspection DuplicatedCode
    async def _subscribe_trades_and_quotes(self):
        network = self.scheduler.get_network()

        for instrument in self.get_instruments():
            symbol = instrument.get_exchange_instrument_code()

            self.instrument_trades[symbol] = MutableSignal()
            self.instrument_order_book_events[symbol] = MutableSignal()
            self.instrument_order_books[symbol] = OrderBookBuilder(network, self.instrument_order_book_events[symbol])

            # magic: inject the bare Signal into the graph so we can
            # fire events on it without any downstream connections
            network.attach(self.instrument_trades[symbol])
            network.attach(self.instrument_order_book_events[symbol])
            network.attach(self.instrument_order_books[symbol])

            trade_subscribe_msg = {
                'id': 1,
                'method': 'trade.subscribe',
                'params': [symbol]
            }

            trade_messages = MutableSignal()
            trade_json_messages = Map(network, trade_messages, lambda x: json.loads(x))
            trade_incr_messages = Filter(network, trade_json_messages,
                                         lambda x: x.get('type', None) == 'incremental')
            trade_lists = Map(network, trade_incr_messages, lambda x: self.__extract_trades(x))
            trades = FlatMap(self.scheduler, trade_lists)

            class TradeScheduler(Event):
                # noinspection PyShadowingNames
                def __init__(self, fh: PhemexFeedHandler, trades: Signal):
                    self.fh = fh
                    self.trades = trades

                def on_activate(self) -> bool:
                    if self.trades.is_valid():
                        trade = self.trades.get_value()
                        trade_symbol = trade.get_instrument().get_exchange_instrument_code()
                        trade_signal = self.fh.instrument_trades[trade_symbol]
                        self.fh.scheduler.schedule_update(trade_signal, trade)
                        return True
                    else:
                        return False

            network.connect(trades, TradeScheduler(self, trades))

            orderbook_subscribe_msg = {
                'id': 2,
                'method': 'orderbook.subscribe',
                'params': [symbol]
            }

            obe_messages = MutableSignal()
            obe_json_messages = Map(network, obe_messages, lambda x: json.loads(x))
            obe_json_messages = Filter(network, obe_json_messages,
                                       lambda x: x.get('type', None) in ['incremental', 'snapshot'])
            order_book_events = Map(network, obe_json_messages, lambda x: self.__extract_order_book_event(x))

            class OrderBookEventScheduler(Event):
                # noinspection PyShadowingNames
                def __init__(self, fh: PhemexFeedHandler, order_book_events: Signal):
                    self.fh = fh
                    self.order_book_events = order_book_events

                def on_activate(self) -> bool:
                    if self.order_book_events.is_valid():
                        obe = self.order_book_events.get_value()
                        obe_symbol = obe.get_instrument().get_exchange_instrument_code()
                        obe_signal = self.fh.instrument_order_book_events[obe_symbol]
                        self.fh.scheduler.schedule_update(obe_signal, obe)
                        return True
                    else:
                        return False

            network.connect(order_book_events, OrderBookEventScheduler(self, order_book_events))

            # noinspection PyShadowingNames
            async def do_subscribe(instrument, subscribe_msg, messages, msg_type):
                async with websockets.connect(self.ws_uri) as sock:
                    subscribe_msg_txt = json.dumps(subscribe_msg)
                    self.logger.info(f'sending {msg_type} subscription request for '
                                     f'{instrument.get_exchange_instrument_code()}')
                    await sock.send(subscribe_msg_txt)
                    while True:
                        self.scheduler.schedule_update(messages, await sock.recv())

            asyncio.ensure_future(do_subscribe(instrument, trade_subscribe_msg, trade_messages, 'trade'))
            asyncio.ensure_future(do_subscribe(instrument, orderbook_subscribe_msg, obe_messages, 'order book'))

        # we are now live
        self.scheduler.schedule_update(self.state, FeedHandlerState.LIVE)

    def __extract_trades(self, msg) -> List[Trade]:
        trade_list = []
        symbol = msg['symbol']

        instrument = self.known_instrument_ids[symbol]
        price_scale = self.price_scaling[symbol]

        for trade in msg['trades']:
            trade_id = trade[0]
            if trade[1] == 'Buy':
                side = self.buy_code
            else:
                side = self.sell_code
            price = float(trade[2]) / pow(10, price_scale)
            qty = float(trade[3])

            trade_list.append(Trade(instrument, trade_id, trade_id, side, qty, price))

        return trade_list

    def __extract_order_book_event(self, msg) -> OrderBookEvent:
        symbol = msg['symbol']
        seq_num = msg['sequence']
        msg_type = msg['type']

        instrument = self.known_instrument_ids[symbol]
        price_scale = self.price_scaling[symbol]

        def to_book_level_list(px_qty_list):
            book_levels = []
            for px_qty in px_qty_list:
                px = float(px_qty[0]) / pow(10, price_scale)
                qty = px_qty[1]
                book_levels.append(BookLevel(px, qty))
            return book_levels

        book = msg['book']
        if msg_type == 'snapshot':
            bids = to_book_level_list(book['bids'])
            asks = to_book_level_list(book['asks'])
            return OrderBookSnapshot(instrument, bids, asks, seq_num)
        else:
            bids = to_book_level_list(book['bids'])
            asks = to_book_level_list(book['asks'])
            return OrderBookUpdate(instrument, bids, asks, seq_num)


def create_fh(scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id):
    return PhemexFeedHandler(scheduler, instrument_cache, instance_id)


def main(instance_id: str = 'prod', journal_path: str = '/behemoth/journals/'):
    ws_fh_main(create_fh, PhemexFeedHandler.get_uri_scheme(), instance_id, journal_path, 'PHEMEX_TRADES')


if __name__ == '__main__':
    fire.Fire(main)
