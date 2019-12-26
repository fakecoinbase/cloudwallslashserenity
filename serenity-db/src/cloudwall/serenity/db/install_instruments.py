import coinbasepro
import gemini
import psycopg2

conn = psycopg2.connect(host="localhost", dbname="serenity", user="postgres", password="password")
cur = conn.cursor()

# get the currency mappings
currency_id_by_code = {}
cur.execute("SELECT currency_id, currency_code FROM serenity.currency")
for currency_code in cur.fetchall():
    currency_id_by_code[currency_code[1]] = currency_code[0]

# get instrument type code table
instrument_type_id_by_code = {}
cur.execute("SELECT instrument_type_id, instrument_type_code FROM serenity.instrument_type")
for instrument_type in cur.fetchall():
    instrument_type_id_by_code[instrument_type[1]] = instrument_type[0]

cur.execute("DELETE FROM serenity.exchange_instrument")
cur.execute("DELETE FROM serenity.cash_instrument")
cur.execute("DELETE FROM serenity.currency_pair")
cur.execute("DELETE FROM serenity.instrument")
conn.commit()


def install_cash_instrument(currency):
    ticker = '{}.CASH'.format(currency)
    cur.execute("INSERT INTO serenity.instrument (instrument_code, instrument_type_id) VALUES (%s, %s)",
                (ticker, instrument_type_id_by_code['Cash']))
    cur.execute("SELECT instrument_id FROM serenity.instrument WHERE instrument_code = %s", (ticker,))
    instrument_id = cur.fetchone()[0]
    cur.execute("INSERT INTO serenity.cash_instrument (currency_id, instrument_id) VALUES (%s, %s)",
                (currency_id_by_code[currency], instrument_id))


def install_currency_pair(base_currency, quote_currency):
    ticker = '{}-{}'.format(base_currency, quote_currency)
    cur.execute("INSERT INTO serenity.instrument (instrument_code, instrument_type_id) VALUES (%s, %s)",
                (ticker, instrument_type_id_by_code['CurrencyPair']))
    cur.execute("SELECT instrument_id FROM serenity.instrument WHERE instrument_code = %s", (ticker,))
    instrument_id = cur.fetchone()[0]
    cur.execute("INSERT INTO serenity.currency_pair (base_currency_id, quote_currency_id, instrument_id) "
                "VALUES (%s, %s, %s)", (currency_id_by_code[base_currency], currency_id_by_code[quote_currency],
                                        instrument_id))


install_cash_instrument("USD")
install_cash_instrument("USDT")
install_cash_instrument("BTC")
install_cash_instrument("LTC")
install_cash_instrument("ETH")
install_cash_instrument("ZEC")
install_cash_instrument("BCH")

install_currency_pair("BTC", "USD")
install_currency_pair("BTC", "USDT")
install_currency_pair("BCH", "USD")
install_currency_pair("BCH", "BTC")
install_currency_pair("BCH", "ETH")
install_currency_pair("LTC", "USD")
install_currency_pair("LTC", "BTC")
install_currency_pair("LTC", "BCH")
install_currency_pair("LTC", "ETH")
install_currency_pair("ETH", "USD")
install_currency_pair("ETH", "BTC")
install_currency_pair("ZEC", "USD")
install_currency_pair("ZEC", "BTC")
install_currency_pair("ZEC", "BCH")
install_currency_pair("ZEC", "ETH")
install_currency_pair("ZEC", "LTC")
install_currency_pair("USDT", "USD")

conn.commit()

# build instrument table
instrument_id_by_code = {}
cur.execute("SELECT instrument_id, instrument_code FROM serenity.instrument")
for instrument in cur.fetchall():
    instrument_id_by_code[instrument[1]] = instrument[0]

# map all Gemini products to exchange_instrument table
gemini_client = gemini.PublicClient()
for symbol in gemini_client.symbols():
    internal_symbol = symbol[0:3].upper() + "-" + symbol[3:].upper()
    internal_id = instrument_id_by_code[internal_symbol]
    cur.execute("INSERT INTO serenity.exchange_instrument (exchange_instrument_code, instrument_id) "
                "VALUES (%s, %s)", (symbol, internal_id))

conn.commit()

cbp_client = coinbasepro.PublicClient()
print(cbp_client.get_products())
