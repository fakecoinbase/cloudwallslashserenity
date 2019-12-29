from abc import ABC


class TypeCodeCache:
    """
    Helper that pre-caches all typecodes in the database and lets the user look up the ID by code.
    """
    def __init__(self, cur):
        self.cur = cur
        self.type_code_map = {
            "exchange": self._load("exchange"),
            "side": self._load("side"),
            "order_type": self._load("order_type"),
            "destination_type": self._load("destination_type"),
            "time_in_force": self._load("time_in_force", "tif_id", "tif_code"),
            "mark_type": self._load("mark_type", "mark_type_id", "mark_code"),
            "exchange_transfer_method": self._load("exchange_transfer_method"),
            "exchange_transfer_type": self._load("exchange_transfer_type"),
            "exchange_transfer_destination_type": self._load("exchange_transfer_destination_type")
        }

    def get_exchange_id(self, exchange_code):
        return self.type_code_map["exchange"][exchange_code]

    def get_side_id(self, side_code):
        return self.type_code_map["side"][side_code]

    def get_order_type_id(self, order_type_code):
        return self.type_code_map["order_type"][order_type_code]

    def get_destination_type_id(self, destination_type_code):
        return self.type_code_map["destination_type"][destination_type_code]

    def get_time_in_force_id(self, tif_code):
        return self.type_code_map["time_in_force"][tif_code]

    def get_mark_type_id(self, mark_code):
        return self.type_code_map["mark_type"][mark_code]

    def get_exchange_transfer_method_id(self, exchange_transfer_method_code):
        return self.type_code_map["exchange_transfer_method"][exchange_transfer_method_code]

    def get_exchange_transfer_type_id(self, exchange_transfer_type_code):
        return self.type_code_map["exchange_transfer_type"][exchange_transfer_type_code]

    def get_exchange_transfer_destination_type_id(self, exchange_transfer_destination_type_code):
        return self.type_code_map["exchange_transfer_destination_type"][exchange_transfer_destination_type_code]

    def _load(self, table_name, id_column_name=None, code_column_name=None):
        if id_column_name is None:
            id_column_name = table_name + '_id'
        if code_column_name is None:
            code_column_name = table_name + '_code'

        type_map = {}
        self.cur.execute("SELECT " + id_column_name + ", " + code_column_name + " FROM serenity." + table_name)
        for row in self.cur.fetchall():
            type_map[row[1]] = row[0]
        return type_map


class InstrumentCache:
    def __init__(self, cur, type_code_cache):
        self.cur = cur
        self.type_code_cache = type_code_cache
        self.instrument_map = {}
        self.currency_map = {}

    def get_or_create_instrument(self, code, instrument_type) -> int:
        self.cur.execute("SELECT instrument_id FROM serenity.instrument WHERE instrument_code = %s", (code,))
        res = self.cur.fetchone()
        if res is not None:
            return res[0]
        else:
            instrument_type_id = self.type_code_cache.get_instrument_type_id(instrument_type)
            self.cur.execute("INSERT INTO serenity.instrument (instrument_code, instrument_type_id) VALUES (%s, %s) "
                             " RETURNING instrument_id", (code, instrument_type_id))
            return self.cur.fetchone()[0]

    def get_or_create_currency(self, currency_code) -> int:
        self.cur.execute("SELECT currency_id FROM serenity.currency WHERE currency_code = %s", (currency_code,))
        res = self.cur.fetchone()
        if res is not None:
            return res[0]
        else:
            self.cur.execute("INSERT INTO serenity.currency (currency_code) VALUES (%s) RETURNING currency_id",
                             (currency_code,))
            currency_id = self.cur.fetchone()[0]
            self.get_or_create_instrument("{}.CASH".format(currency_code), "Cash")
            return currency_id

    def get_or_create_currency_pair(self, base_ccy_code, quote_ccy_code) -> int:
        base_ccy_id = self.get_or_create_currency(base_ccy_code)
        quote_ccy_id = self.get_or_create_currency(quote_ccy_code)
        instrument_code = "{}-{}".format(base_ccy_code, quote_ccy_code)
        self.cur.execute("SELECT instrument_id FROM serenity.currency_pair WHERE base_currency_id = %s "
                         "AND quote_currency_id = %s", (base_ccy_id, quote_ccy_id))
        res = self.cur.fetchone()
        if res is not None:
            return res[0]
        else:
            instrument_id = self.get_or_create_instrument(instrument_code, "CurrencyPair")
            self.cur.execute("INSERT INTO serenity.currency_pair (base_currency_id, quote_currency_id, instrument_id) "
                             "VALUES (%s, %s, %s)", (base_ccy_id, quote_ccy_id, instrument_id))
            return instrument_id

    def get_or_create_exchange_instrument(self, exchange_symbol, instrument_id, exchange_code) -> int:
        self.cur.execute("SELECT exchange_instrument_id FROM serenity.exchange_instrument "
                         "WHERE exchange_instrument_code = %s", (exchange_symbol,))
        res = self.cur.fetchone()
        if res is not None:
            return res[0]
        else:
            exchange_id = self.type_code_cache.get_exchange_id(exchange_code)
            self.cur.execute("INSERT INTO serenity.exchange_instrument (exchange_instrument_code, instrument_id, "
                             "exchange_id) VALUES (%s, %s, %s) RETURNING exchange_instrument_id",
                             (exchange_symbol, instrument_id, exchange_id))
            return self.cur.fetchone()[0]
