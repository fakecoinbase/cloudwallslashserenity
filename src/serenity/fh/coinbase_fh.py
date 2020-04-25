import json

import coinbasepro
import fire
import websockets
from tau.core import MutableSignal, NetworkScheduler
from tau.signal import Map, Filter

from serenity.db import TypeCodeCache, InstrumentCache
from serenity.fh.feedhandler import FeedState, WebsocketFeedHandler, WebsocketFeed, ws_fh_main
from serenity.model.exchange import ExchangeInstrument
from serenity.model.marketdata import Trade


class CoinbaseProFeed(WebsocketFeed):
    def __init__(self, scheduler: NetworkScheduler, type_code_cache: TypeCodeCache, ws_uri: str,
                 exch_instrument: ExchangeInstrument):
        super().__init__(scheduler, type_code_cache, ws_uri, exch_instrument)

    async def _subscribe_trades_and_quotes(self):
        subscribe_msg = {
            'type': 'subscribe',
            'product_ids': [f'{self.instrument.get_exchange_instrument_code()}'],
            'channels': ['matches', 'heartbeat']
        }

        network = self.scheduler.get_network()

        messages = MutableSignal()
        json_messages = Map(network, messages, lambda x: json.loads(x))
        match_messages = Filter(network, json_messages, lambda x: x.get('type', None) == 'match')
        self.trades = Map(network, match_messages, lambda x: self._extract_trade(x))

        # self.trades is now valid, transition into LIVE state
        self.scheduler.schedule_update(self.feed_state, FeedState.LIVE)

        async with websockets.connect(self.ws_uri) as sock:
            await sock.send(json.dumps(subscribe_msg))
            while True:
                self.scheduler.schedule_update(messages, await sock.recv())

    def _extract_trade(self, msg) -> Trade:
        sequence = msg['sequence']
        trade_id = msg['trade_id']
        side = self.buy_code if msg['side'] == 'buy' else self.sell_code
        qty = float(msg['size'])
        price = float(msg['price'])

        return Trade(self.get_instrument(), sequence, trade_id, side, qty, price)


class CoinbaseProFeedHandler(WebsocketFeedHandler):
    def __init__(self, scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id: str = 'prod'):
        if instance_id == 'prod':
            self.ws_uri = 'wss://ws-feed.pro.coinbase.com'
            self.cbp_client = coinbasepro.PublicClient()
        elif instance_id == 'test':
            self.ws_uri = 'wss://ws-feed-public.sandbox.pro.coinbase.com'
            self.cbp_client = coinbasepro.PublicClient(api_url='https://api-public.sandbox.pro.coinbase.com')
        else:
            raise ValueError(f'Unknown instance_id: {instance_id}')

        # ensure we've initialized PhemexConnection before loading instruments in super()
        super().__init__(scheduler, instrument_cache, instance_id)

    @staticmethod
    def get_uri_scheme() -> str:
        return 'coinbasepro'

    def _create_feed(self, scheduler, type_code_cache: TypeCodeCache, instrument: ExchangeInstrument):
        return CoinbaseProFeed(scheduler, type_code_cache, self.ws_uri, instrument)

    def _load_instruments(self):
        self.logger.info("Downloading supported products")

        for product in self.cbp_client.get_products():
            symbol = product['id']
            base_ccy = product['base_currency']
            quote_ccy = product['quote_currency']
            currency_pair = self.instrument_cache.get_or_create_currency_pair(base_ccy, quote_ccy)
            instrument = currency_pair.get_instrument()
            exch_instr = self.instrument_cache.get_or_create_exchange_instrument(symbol, instrument, "CoinbasePro")

            self.logger.info(f'\t{symbol} - {base_ccy}/{quote_ccy} [ID #{instrument.get_instrument_id()}]')
            self.known_instrument_ids[symbol] = exch_instr
            self.instruments.append(exch_instr)


def create_fh(scheduler: NetworkScheduler, instrument_cache: InstrumentCache, instance_id):
    return CoinbaseProFeedHandler(scheduler, instrument_cache, instance_id)


def main(instance_id: str = 'prod', journal_path: str = '/behemoth/journals/'):
    # due to limitation in current implementation we cannot handle more than a limited number of symbols without causing
    # Coinbase Pro to reject our connections; in theory we should be able to open one connection and keep sending
    # it incremental subscribe messages but the way the code is structured and the way websockets works I am not sure
    # how to do this
    ws_fh_main(create_fh, CoinbaseProFeedHandler.get_uri_scheme(), instance_id, journal_path, 'COINBASE_PRO_TRADES',
               include_symbols={'BTC-USD', 'ETH-USD', 'LTC-USD'})


if __name__ == '__main__':
    fire.Fire(main)
