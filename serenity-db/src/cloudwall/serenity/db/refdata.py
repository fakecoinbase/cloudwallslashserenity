from cloudwall.serenity.model.exchange import Exchange, ExchangeTransferMethod, ExchangeTransferType, \
    ExchangeTransferDestinationType, ExchangeInstrument
from cloudwall.serenity.model.instrument import InstrumentType, Instrument, Currency, CurrencyPair, CashInstrument
from cloudwall.serenity.model.mark import MarkType
from cloudwall.serenity.model.order import Side, OrderType, DestinationType, TimeInForce


class TypeCodeCache:
    """
    Helper that pre-caches all typecodes in the database and lets the user look up the ID by code.
    """
    def __init__(self, cur):
        self.cur = cur
        self.type_code_map = {
            Exchange: self._load("exchange", Exchange),
            InstrumentType: self._load("instrument_type", InstrumentType),
            Side: self._load("side", Side),
            OrderType: self._load("order_type", OrderType),
            DestinationType: self._load("destination_type", DestinationType),
            TimeInForce: self._load("time_in_force", TimeInForce),
            MarkType: self._load("mark_type", MarkType),
            ExchangeTransferMethod: self._load("exchange_transfer_method", ExchangeTransferMethod),
            ExchangeTransferType: self._load("exchange_transfer_type", ExchangeTransferType),
            ExchangeTransferDestinationType: self._load("exchange_transfer_destination_type",
                                                        ExchangeTransferDestinationType)
        }

    def get_by_code(self, klass, type_code):
        return self.type_code_map[klass][0][type_code]

    def get_by_id(self, klass, type_id):
        return self.type_code_map[klass][1][type_id]

    def _load(self, table_name, klass):
        id_column_name = table_name + '_id'
        code_column_name = table_name + '_code'

        type_by_code = {}
        type_by_id = {}
        self.cur.execute("SELECT " + id_column_name + ", " + code_column_name + " FROM serenity." + table_name)
        for row in self.cur.fetchall():
            type_obj = klass(row[0], row[1])
            type_by_code[row[1]] = type_obj
            type_by_id[row[0]] = type_obj
        return type_by_code, type_by_id


class InstrumentCache:
    def __init__(self, cur, type_code_cache: TypeCodeCache):
        self.cur = cur
        self.type_code_cache = type_code_cache

        self.entity_by_id = {
            Currency: {},
            Instrument: {},
            CashInstrument: {},
            CurrencyPair: {},
            ExchangeInstrument: {}
        }
        self.entity_by_ak = {
            Currency: {},
            Instrument: {},
            CashInstrument: {},
            CurrencyPair: {},
            ExchangeInstrument: {}
        }

        self.cur.execute("SELECT currency_id, currency_code FROM serenity.currency")
        for row in self.cur.fetchall():
            currency = Currency(row[0], row[1])
            self.entity_by_id[Currency][row[0]] = currency
            self.entity_by_ak[Currency][row[1]] = currency

        self.cur.execute("SELECT instrument_id, instrument_type_id, instrument_code FROM serenity.instrument")
        for row in self.cur.fetchall():
            instrument_type = self.type_code_cache.get_by_id(InstrumentType, row[1])
            instrument = Instrument(row[0], instrument_type, row[2])
            self.entity_by_id[Instrument][row[0]] = instrument
            self.entity_by_ak[Instrument][row[2]] = instrument

        self.cur.execute("SELECT cash_instrument_id, instrument_id, currency_id FROM serenity.cash_instrument")
        for row in self.cur.fetchall():
            cash_instrument_id = row[0]
            instrument = self.entity_by_id[Instrument][row[1]]
            ccy = self.entity_by_id[Currency][row[2]]
            cash_instrument = CashInstrument(cash_instrument_id, instrument, ccy)
            self.entity_by_id[CashInstrument][row[0]] = cash_instrument
            self.entity_by_ak[CashInstrument][ccy.get_currency_code()] = cash_instrument

        self.cur.execute("SELECT currency_pair_id, instrument_id, base_currency_id, quote_currency_id "
                         "FROM serenity.currency_pair")
        for row in self.cur.fetchall():
            currency_pair_id = row[0]
            instrument = self.entity_by_id[Instrument][row[1]]
            base_ccy = self.entity_by_id[Currency][row[2]]
            quote_ccy = self.entity_by_id[Currency][row[3]]
            ccy_pair = CurrencyPair(currency_pair_id, instrument, base_ccy, quote_ccy)
            self.entity_by_id[CurrencyPair][currency_pair_id] = ccy_pair
            self.entity_by_ak[CurrencyPair][(row[2], row[3])] = ccy_pair

        self.cur.execute("SELECT exchange_instrument_id, instrument_id, exchange_id, exchange_instrument_code "
                         "FROM serenity.exchange_instrument")
        for row in self.cur.fetchall():
            exchange_instrument_id = row[0]
            instrument = self.entity_by_id[Instrument][row[1]]
            exchange = self.type_code_cache.get_by_id(Exchange, row[2])
            exchange_instrument_code = row[3]
            exch_instr = ExchangeInstrument(exchange_instrument_id, exchange, instrument, exchange_instrument_code)
            self.entity_by_id[ExchangeInstrument][exchange_instrument_id] = exch_instr
            self.entity_by_ak[ExchangeInstrument][(exchange.get_type_code(), exchange_instrument_code)] = exch_instr

    def get_or_create_instrument(self, code: str, instrument_type: InstrumentType) -> Instrument:
        if code in self.entity_by_ak[Instrument]:
            return self.entity_by_ak[Instrument][code]
        else:
            self.cur.execute("INSERT INTO serenity.instrument (instrument_code, instrument_type_id) VALUES (%s, %s) "
                             " RETURNING instrument_id", (code, instrument_type.get_type_id()))
            instrument_id = self.cur.fetchone()[0]
            instrument = Instrument(instrument_id, instrument_type, code)
            self.entity_by_id[Instrument][instrument_id] = instrument
            self.entity_by_ak[Instrument][code] = instrument
            return instrument

    def get_or_create_currency(self, currency_code) -> Currency:
        if currency_code in self.entity_by_ak[Currency]:
            return self.entity_by_ak[Currency][currency_code]
        else:
            self.cur.execute("INSERT INTO serenity.currency (currency_code) VALUES (%s) RETURNING currency_id",
                             (currency_code,))
            currency_id = self.cur.fetchone()[0]
            currency = Currency(currency_id, currency_code)
            self.entity_by_id[Currency][currency_id] = currency
            self.entity_by_ak[Currency][currency_code] = currency

            # create corresponding entry in the cash_instrument table
            self.get_or_create_cash_instrument(currency_code)

            return currency

    def get_or_create_cash_instrument(self, currency_code: str) -> CashInstrument:
        if currency_code in self.entity_by_ak[CashInstrument]:
            return self.entity_by_ak[CashInstrument][currency_code]
        else:
            instrument_code = "{}.CASH".format(currency_code)
            instrument_type = self.type_code_cache.get_by_code(InstrumentType, "Cash")
            instrument = self.get_or_create_instrument(instrument_code, instrument_type)
            currency = self.get_or_create_currency(currency_code)
            self.cur.execute("INSERT INTO serenity.cash_instrument (currency_id, instrument_id) "
                             "VALUES (%s, %s) RETURNING cash_instrument_id", (currency.get_currency_id(),
                                                                              instrument.get_instrument_id()))
            cash_instrument_id = self.cur.fetchone()[0]
            cash_instrument = CashInstrument(cash_instrument_id, instrument, currency)
            self.entity_by_id[CashInstrument][cash_instrument_id] = cash_instrument
            self.entity_by_ak[CashInstrument][currency_code] = cash_instrument
            return cash_instrument

    def get_or_create_currency_pair(self, base_ccy_code, quote_ccy_code) -> CurrencyPair:
        base_ccy = self.get_or_create_currency(base_ccy_code)
        quote_ccy = self.get_or_create_currency(quote_ccy_code)
        pair = (base_ccy_code, quote_ccy_code)
        if pair in self.entity_by_ak[CurrencyPair]:
            return self.entity_by_ak[CurrencyPair][pair]
        else:
            instrument_code = "{}-{}".format(base_ccy_code, quote_ccy_code)
            instrument_type = self.type_code_cache.get_by_code(InstrumentType, "CurrencyPair")
            instrument = self.get_or_create_instrument(instrument_code, instrument_type)
            self.cur.execute("INSERT INTO serenity.currency_pair (base_currency_id, quote_currency_id, instrument_id) "
                             "VALUES (%s, %s, %s) RETURNING currency_pair_id", (base_ccy.get_currency_id(),
                                                                                quote_ccy.get_currency_id(),
                                                                                instrument.get_instrument_id()))
            currency_pair_id = self.cur.fetchone()[0]
            ccy_pair = CurrencyPair(currency_pair_id, instrument, base_ccy, quote_ccy)
            self.entity_by_id[CurrencyPair][currency_pair_id] = ccy_pair
            self.entity_by_ak[CurrencyPair][pair] = ccy_pair
            return ccy_pair

    def get_or_create_exchange_instrument(self, exchange_symbol, instrument, exchange_code) -> ExchangeInstrument:
        ak = (exchange_code, exchange_symbol)
        if ak in self.entity_by_ak[ExchangeInstrument]:
            return self.entity_by_ak[ExchangeInstrument][ak]
        else:
            exchange = self.type_code_cache.get_by_code(Exchange, exchange_code)
            self.cur.execute("INSERT INTO serenity.exchange_instrument (exchange_instrument_code, instrument_id, "
                             "exchange_id) VALUES (%s, %s, %s) RETURNING exchange_instrument_id",
                             (exchange_symbol, instrument.get_instrument_id(), exchange.get_type_id()))
            exchange_instrument_id = self.cur.fetchone()[0]
            exchange_instrument = ExchangeInstrument(exchange_instrument_id, exchange, instrument, exchange_symbol)
            self.entity_by_id[ExchangeInstrument][exchange_instrument_id] = exchange_instrument
            self.entity_by_ak[ExchangeInstrument][ak] = exchange_instrument
            return exchange_instrument

    def get_entity_by_id(self, klass, entity_id):
        return self.entity_by_id[klass][entity_id]