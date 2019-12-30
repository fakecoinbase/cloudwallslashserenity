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
            "exchange": self._load("exchange", Exchange),
            "instrument_type": self._load("instrument_type", InstrumentType),
            "side": self._load("side", Side),
            "order_type": self._load("order_type", OrderType),
            "destination_type": self._load("destination_type", DestinationType),
            "time_in_force": self._load("time_in_force", TimeInForce),
            "mark_type": self._load("mark_type", MarkType),
            "exchange_transfer_method": self._load("exchange_transfer_method", ExchangeTransferMethod),
            "exchange_transfer_type": self._load("exchange_transfer_type", ExchangeTransferType),
            "exchange_transfer_destination_type": self._load("exchange_transfer_destination_type",
                                                             ExchangeTransferDestinationType)
        }

    def get_exchange(self, exchange_code) -> Exchange:
        return self.type_code_map["exchange"][exchange_code]

    def get_instrument_type(self, instrument_type_code) -> InstrumentType:
        return self.type_code_map["instrument_type"][instrument_type_code]

    def get_side(self, side_code) -> Side:
        return self.type_code_map["side"][side_code]

    def get_order_type(self, order_type_code) -> OrderType:
        return self.type_code_map["order_type"][order_type_code]

    def get_destination_type(self, destination_type_code) -> DestinationType:
        return self.type_code_map["destination_type"][destination_type_code]

    def get_time_in_force(self, tif_code) -> TimeInForce:
        return self.type_code_map["time_in_force"][tif_code]

    def get_mark_type(self, mark_type_code) -> MarkType:
        return self.type_code_map["mark_type"][mark_type_code]

    def get_exchange_transfer_method(self, exchange_transfer_method_code) -> ExchangeTransferMethod:
        return self.type_code_map["exchange_transfer_method"][exchange_transfer_method_code]

    def get_exchange_transfer_type(self, exchange_transfer_type_code) -> ExchangeTransferType:
        return self.type_code_map["exchange_transfer_type"][exchange_transfer_type_code]

    def get_exchange_transfer_destination_type(self, exchange_transfer_destination_type_code) \
            -> ExchangeTransferDestinationType:
        return self.type_code_map["exchange_transfer_destination_type"][exchange_transfer_destination_type_code]

    def _load(self, table_name, klass, id_column_name=None, code_column_name=None):
        if id_column_name is None:
            id_column_name = table_name + '_id'
        if code_column_name is None:
            code_column_name = table_name + '_code'

        type_map = {}
        self.cur.execute("SELECT " + id_column_name + ", " + code_column_name + " FROM serenity." + table_name)
        for row in self.cur.fetchall():
            type_map[row[1]] = klass(row[0], row[1])
        return type_map


class InstrumentCache:
    def __init__(self, cur, type_code_cache: TypeCodeCache):
        self.cur = cur
        self.type_code_cache = type_code_cache

        self.instrument_by_code = {}
        self.currency_by_code = {}
        self.currency_pair_by_pair = {}
        self.cash_instrument_by_ccy = {}
        self.exchange_instrument_by_code = {}

        self.cur.execute("SELECT currency_id, currency_code FROM serenity.currency")
        for row in self.cur.fetchall():
            self.currency_by_code[row[1]] = Currency(row[0], row[1])

        self.cur.execute("SELECT instrument_id, t.instrument_type_code, instrument_code FROM serenity.instrument i "
                         "INNER JOIN serenity.instrument_type t ON t.instrument_type_id = i.instrument_type_id")
        for row in self.cur.fetchall():
            instrument_type = self.type_code_cache.get_instrument_type(row[1])
            instrument = Instrument(row[0], instrument_type, row[2])
            self.instrument_by_code[row[2]] = instrument

        self.cur.execute("SELECT cash_instrument_id, i.instrument_code, ccy.currency_code "
                         "FROM serenity.cash_instrument c "
                         "INNER JOIN serenity.instrument i ON i.instrument_id = c.instrument_id "
                         "INNER JOIN serenity.currency ccy ON ccy.currency_id = c.currency_id")
        for row in self.cur.fetchall():
            cash_instrument_id = row[0]
            instrument = self.instrument_by_code[row[1]]
            ccy = self.currency_by_code[row[2]]
            self.cash_instrument_by_ccy[row[2]] = CashInstrument(cash_instrument_id, instrument, ccy)

        self.cur.execute("SELECT currency_pair_id, i.instrument_code, ccy1.currency_code, ccy2.currency_code "
                         "FROM serenity.currency_pair p "
                         "INNER JOIN serenity.instrument i ON i.instrument_id = p.instrument_id "
                         "INNER JOIN serenity.currency ccy1 ON ccy1.currency_id = p.base_currency_id "
                         "INNER JOIN serenity.currency ccy2 ON ccy2.currency_id = p.quote_currency_id")
        for row in self.cur.fetchall():
            currency_pair_id = row[0]
            instrument = self.instrument_by_code[row[1]]
            base_ccy = self.currency_by_code[row[2]]
            quote_ccy = self.currency_by_code[row[3]]
            self.currency_pair_by_pair[(row[2], row[3])] = CurrencyPair(currency_pair_id, instrument, 
                                                                        base_ccy, quote_ccy)

        self.cur.execute("SELECT exchange_instrument_id, i.instrument_code, e.exchange_code, exchange_instrument_code "
                         "FROM serenity.exchange_instrument ei "
                         "INNER JOIN serenity.instrument i ON i.instrument_id = ei.instrument_id "
                         "INNER JOIN serenity.exchange e ON e.exchange_id = ei.exchange_id")
        for row in self.cur.fetchall():
            exchange_instrument_id = row[0]
            instrument = self.instrument_by_code[row[1]]
            exchange = self.type_code_cache.get_exchange(row[2])
            exchange_instrument_code = row[3]
            self.exchange_instrument_by_code[exchange_instrument_code] = ExchangeInstrument(exchange_instrument_id,
                                                                                            exchange, instrument,
                                                                                            exchange_instrument_code)

    def get_or_create_instrument(self, code: str, instrument_type: InstrumentType) -> Instrument:
        if code in self.instrument_by_code:
            return self.instrument_by_code[code]
        else:
            self.cur.execute("INSERT INTO serenity.instrument (instrument_code, instrument_type_id) VALUES (%s, %s) "
                             " RETURNING instrument_id", (code, instrument_type.get_type_id()))
            instrument_id = self.cur.fetchone()[0]
            instrument = Instrument(instrument_id, instrument_type, code)
            self.instrument_by_code[code] = instrument
            return instrument

    def get_or_create_currency(self, currency_code) -> Currency:
        if currency_code in self.currency_by_code:
            return self.currency_by_code[currency_code]
        else:
            self.cur.execute("INSERT INTO serenity.currency (currency_code) VALUES (%s) RETURNING currency_id",
                             (currency_code,))
            currency_id = self.cur.fetchone()[0]
            currency = Currency(currency_id, currency_code)
            self.currency_by_code[currency_code] = currency

            # create corresponding entry in the cash_instrument table
            self.get_or_create_cash_instrument(currency_code)

            return currency

    def get_or_create_cash_instrument(self, currency_code: str) -> CashInstrument:
        if currency_code in self.cash_instrument_by_ccy:
            return self.cash_instrument_by_ccy[currency_code]
        else:
            instrument_code = "{}.CASH".format(currency_code)
            instrument_type = self.type_code_cache.get_instrument_type("Cash")
            instrument = self.get_or_create_instrument(instrument_code, instrument_type)
            currency = self.get_or_create_currency(currency_code)
            self.cur.execute("INSERT INTO serenity.cash_instrument (currency_id, instrument_id) "
                             "VALUES (%s, %s) RETURNING cash_instrument_id", (currency.get_currency_id(),
                                                                              instrument.get_instrument_id()))
            cash_instrument_id = self.cur.fetchone()[0]
            cash_instrument = CashInstrument(cash_instrument_id, instrument, currency)
            self.cash_instrument_by_ccy[currency_code] = cash_instrument
            return cash_instrument

    def get_or_create_currency_pair(self, base_ccy_code, quote_ccy_code) -> CurrencyPair:
        base_ccy = self.get_or_create_currency(base_ccy_code)
        quote_ccy = self.get_or_create_currency(quote_ccy_code)
        pair = (base_ccy_code, quote_ccy_code)
        if pair in self.currency_pair_by_pair:
            return self.currency_pair_by_pair[pair]
        else:
            instrument_code = "{}-{}".format(base_ccy_code, quote_ccy_code)
            instrument_type = self.type_code_cache.get_instrument_type("CurrencyPair")
            instrument = self.get_or_create_instrument(instrument_code, instrument_type)
            self.cur.execute("INSERT INTO serenity.currency_pair (base_currency_id, quote_currency_id, instrument_id) "
                             "VALUES (%s, %s, %s) RETURNING currency_pair_id", (base_ccy.get_currency_id(),
                                                                                quote_ccy.get_currency_id(),
                                                                                instrument.get_instrument_id()))
            currency_pair_id = self.cur.fetchone()[0]
            ccy_pair = CurrencyPair(currency_pair_id, instrument, base_ccy, quote_ccy)
            self.currency_pair_by_pair[pair] = ccy_pair
            return ccy_pair

    def get_or_create_exchange_instrument(self, exchange_symbol, instrument, exchange_code) -> ExchangeInstrument:
        if exchange_symbol in self.exchange_instrument_by_code:
            return self.exchange_instrument_by_code[exchange_symbol]
        else:
            exchange = self.type_code_cache.get_exchange(exchange_code)
            self.cur.execute("INSERT INTO serenity.exchange_instrument (exchange_instrument_code, instrument_id, "
                             "exchange_id) VALUES (%s, %s, %s) RETURNING exchange_instrument_id",
                             (exchange_symbol, instrument.get_instrument_id(), exchange.get_type_id()))
            exchange_instrument_id = self.cur.fetchone()[0]
            exchange_instrument = ExchangeInstrument(exchange_instrument_id, exchange, instrument, exchange_symbol)
            self.exchange_instrument_by_code[exchange_symbol] = exchange_instrument
            return exchange_instrument
