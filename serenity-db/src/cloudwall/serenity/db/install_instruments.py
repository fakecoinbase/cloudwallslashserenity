import binance.client
import coinbasepro
import gemini
from cloudwall.serenity.db import connect_serenity_db


def get_or_create_instrument(cursor, code, instrument_type) -> int:
    cursor.execute("SELECT instrument_type_id FROM serenity.instrument_type WHERE instrument_type_code = %s",
                   (instrument_type,))
    instrument_type_id = cursor.fetchone()[0]

    cursor.execute("SELECT instrument_id FROM serenity.instrument WHERE instrument_code = %s", (code,))
    res = cursor.fetchone()
    if res is not None:
        return res[0]
    else:
        cursor.execute("INSERT INTO serenity.instrument (instrument_code, instrument_type_id) VALUES (%s, %s) "
                       " RETURNING instrument_id", (code, instrument_type_id))
        return cursor.fetchone()[0]


def get_or_create_currency(cursor, currency_code) -> int:
    cursor.execute("SELECT currency_id FROM serenity.currency WHERE currency_code = %s", (currency_code,))
    res = cursor.fetchone()
    if res is not None:
        return res[0]
    else:
        cursor.execute("INSERT INTO serenity.currency (currency_code) VALUES (%s) RETURNING currency_id",
                       (currency_code,))
        currency_id = cursor.fetchone()[0]
        get_or_create_instrument(cursor, "{}.CASH".format(currency_code), "Cash")
        return currency_id


def get_or_create_currency_pair(cursor, base_ccy_code, quote_ccy_code) -> int:
    base_ccy_id = get_or_create_currency(cursor, base_ccy_code)
    quote_ccy_id = get_or_create_currency(cursor, quote_ccy_code)
    instrument_code = "{}-{}".format(base_ccy_code, quote_ccy_code)
    cursor.execute("SELECT instrument_id FROM serenity.currency_pair WHERE base_currency_id = %s "
                   "AND quote_currency_id = %s", (base_ccy_id, quote_ccy_id))
    res = cursor.fetchone()
    if res is not None:
        return res[0]
    else:
        instrument_id = get_or_create_instrument(cursor, instrument_code, "CurrencyPair")
        cursor.execute("INSERT INTO serenity.currency_pair (base_currency_id, quote_currency_id, instrument_id) "
                       "VALUES (%s, %s, %s) RETURNING currency_pair_id", (base_ccy_id, quote_ccy_id, instrument_id))
        return instrument_id


def get_or_create_exchange_instrument(cursor, exchange_symbol, instrument_id, exchange_code) -> int:
    cursor.execute("SELECT exchange_instrument_id FROM serenity.exchange_instrument "
                   "WHERE exchange_instrument_code = %s", (exchange_symbol,))
    res = cursor.fetchone()
    if res is not None:
        return res[0]
    else:
        cursor.execute("SELECT exchange_id FROM serenity.exchange WHERE exchange_code = %s", (exchange_code,))
        exchange_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO serenity.exchange_instrument (exchange_instrument_code, instrument_id, "
                       "exchange_id) VALUES (%s, %s, %s) RETURNING exchange_instrument_id",
                       (exchange_symbol, instrument_id, exchange_id))
        return cursor.fetchone()[0]


conn = connect_serenity_db()
conn.autocommit = True
cur = conn.cursor()

# map all Gemini products to exchange_instrument table
gemini_client = gemini.PublicClient()
for symbol in gemini_client.symbols():
    base_ccy = symbol[0:3].upper()
    quote_ccy = symbol[3:].upper()
    internal_id = get_or_create_currency_pair(cur, base_ccy, quote_ccy)
    get_or_create_exchange_instrument(cur, symbol, internal_id, "Gemini")

# map all Coinbase Pro products to exchange_instrument table
cbp_client = coinbasepro.PublicClient()
for product in cbp_client.get_products():
    symbol = product['id']
    base_ccy = product['base_currency']
    quote_ccy = product['quote_currency']
    internal_id = get_or_create_currency_pair(cur, base_ccy, quote_ccy)
    get_or_create_exchange_instrument(cur, symbol, internal_id, "CoinbasePro")

# map all Binance products to exchange_instrument table
binance_client = binance.client.Client()
for product in binance_client.get_products()['data']:
    symbol = product['symbol']
    base_ccy = product['baseAsset']
    quote_ccy = product['quoteAsset']
    internal_id = get_or_create_currency_pair(cur, base_ccy, quote_ccy)
    get_or_create_exchange_instrument(cur, symbol, internal_id, "Binance")
