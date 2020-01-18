import decimal

import fire

from cloudwall.serenity.db import connect_serenity_db, TypeCodeCache, InstrumentCache
from cloudwall.serenity.model.exchange import ExchangeInstrument
from cloudwall.serenity.model.instrument import Instrument, CurrencyPair, Currency
from cloudwall.serenity.model.order import Side


class TradeAnalyzer:
    def __init__(self, cur, type_code_cache: TypeCodeCache, instrument_cache: InstrumentCache):
        self.cur = cur
        self.type_code_cache = type_code_cache
        self.instrument_cache = instrument_cache

        self.trades = {}

        cur.execute("SELECT eo.side_id, eo.exchange_instrument_id, ef.fill_price, ef.quantity, ef.fees, ef.create_time "
                    "FROM serenity.exchange_fill ef "
                    "INNER JOIN serenity.exchange_order eo on eo.exchange_order_id = ef.exchange_order_id "
                    "ORDER BY ef.create_time ASC ")
        for row in cur.fetchall():
            side = type_code_cache.get_by_id(Side, row[0])
            instrument = instrument_cache.get_entity_by_id(ExchangeInstrument, row[1])
            instrument_code = instrument.get_instrument().get_instrument_code()

            if instrument_code not in self.trades:
                self.trades[instrument_code] = {}

            if side.get_type_code() not in self.trades[instrument_code]:
                self.trades[instrument_code][side.get_type_code()] = []

            trade_info = {
                'px': row[2],
                'qty': row[3],
                'remaining': row[3],
                'fee': row[4],
                'ts': row[5],
            }
            self.trades[instrument_code][side.get_type_code()].append(trade_info)

        # explode cross-currency trades into their component parts
        usd_ccy = instrument_cache.get_entity_by_ak(Currency, 'USD')
        for instrument_code in list(self.trades):
            pair_codes = tuple(instrument_code.split('-'))
            base_ccy = instrument_cache.get_entity_by_ak(Currency, pair_codes[0])
            quote_ccy = instrument_cache.get_entity_by_ak(Currency, pair_codes[1])
            if quote_ccy.get_currency_code() != 'USD':
                long = "{}-{}".format(base_ccy.get_currency_code(), usd_ccy.get_currency_code())
                short = "{}-{}".format(quote_ccy.get_currency_code(), usd_ccy.get_currency_code())

                if long not in self.trades:
                    self.trades[long] = {'Buy': [], 'Sell': []}

                if short not in self.trades:
                    self.trades[short] = {'Buy': [], 'Sell': []}

                # for each sell, buy short instrument and sell long instrument
                for sell in self.trades[instrument_code]['Sell']:
                    self.trades[short]['Buy'].append({
                        'px': 0.0,
                        'qty': sell['qty'],
                        'remaining': sell['remaining'],
                        'fee': 0.0,
                        'ts': sell['ts'],
                    })

                    self.trades[long]['Sell'].append({
                        'px': 0.0,
                        'qty': sell['qty'] * sell['px'],
                        'remaining': sell['remaining'],
                        'fee': 0.0,
                        'ts': sell['ts'],
                    })

                    print("Added buy & sell trades at " + str(sell['ts']) + " for Sell of " + instrument_code)

                # for each buy, buy long instrument and sell short instrument
                for buy in self.trades[instrument_code]['Buy']:
                    self.trades[long]['Buy'].append({
                        'px': 0.0,
                        'qty': buy['qty'],
                        'remaining': buy['remaining'],
                        'fee': 0.0,
                        'ts': buy['ts'],
                    })

                    self.trades[short]['Sell'].append({
                        'px': 0.0,
                        'qty': buy['qty'] * buy['px'],
                        'remaining': buy['remaining'],
                        'fee': 0.0,
                        'ts': buy['ts'],
                    })

                    print("Added buy & sell trades at " + str(buy['ts']) + " for Buy of " + instrument_code)

        # re-sort buys and sells by ts
        for instrument_code in list(self.trades):
            self.trades[instrument_code]['Buy'] = sorted(self.trades[instrument_code]['Buy'], key=lambda k: k['ts'])
            self.trades[instrument_code]['Sell'] = sorted(self.trades[instrument_code]['Sell'], key=lambda k: k['ts'])

    def run_analysis(self, instrument_code):
        all_trades = self.trades[instrument_code]
        sells = (all_trades['Sell'])

        for sell in sells:
            print("Sell " + instrument_code.split('-')[0] + " " + str(sell['qty']) + " @ " + str(sell['px']) +
                  " (" + str(sell['ts']) + ")")
            for candidate_buy in all_trades['Buy']:
                if candidate_buy['ts'] <= sell['ts'] and candidate_buy['remaining'] > 0.0 and sell['remaining'] > 0.0:
                    if candidate_buy['remaining'] < sell['remaining']:
                        sell['remaining'] -= candidate_buy['remaining']
                        candidate_buy['remaining'] = decimal.Decimal(0.0)
                    else:
                        candidate_buy['remaining'] -= sell['remaining']
                        sell['remaining'] = decimal.Decimal(0.0)

                    print("\t Buy " + str(candidate_buy['qty']) + " @ " + str(candidate_buy['px']) +
                          " (" + str(candidate_buy['ts']) + "); buy remaining: " + str(candidate_buy['remaining']) +
                          "; sell remaining: " + str(sell['remaining']))


def generate_tax_report():
    conn = connect_serenity_db()
    cur = conn.cursor()
    type_code_cache = TypeCodeCache(cur)
    instrument_cache = InstrumentCache(cur, type_code_cache)

    analyzer = TradeAnalyzer(cur, type_code_cache, instrument_cache)
    analyzer.run_analysis('BTC-USD')


if __name__ == '__main__':
    fire.Fire(generate_tax_report)

