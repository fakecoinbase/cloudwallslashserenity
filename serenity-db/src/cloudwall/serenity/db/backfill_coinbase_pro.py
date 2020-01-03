import coinbasepro
import fire

from cloudwall.serenity.db import connect_serenity_db
from cloudwall.serenity.db.refdata import TypeCodeCache, InstrumentCache
from cloudwall.serenity.model.exchange import ExchangeAccount, ExchangeOrder, Exchange, ExchangeFill, ExchangeInstrument
from cloudwall.serenity.model.instrument import InstrumentType
from cloudwall.serenity.model.order import Side, OrderType, TimeInForce


class ExchangeService:
    def __init__(self, cur, type_code_cache: TypeCodeCache, instrument_cache: InstrumentCache):
        self.cur = cur
        self.type_code_cache = type_code_cache
        self.instrument_cache = instrument_cache

        self.entity_by_id = {
            ExchangeAccount: {},
            ExchangeOrder: {},
            ExchangeFill: {}
        }
        self.entity_by_ak = {
            ExchangeAccount: {},
            ExchangeOrder: {},
            ExchangeFill: {}
        }

        self.cur.execute("SELECT exchange_account_id, exchange_id, exchange_account_num "
                         "FROM serenity.exchange_account")
        for row in self.cur.fetchall():
            exchange = self.type_code_cache.get_by_id(Exchange, row[1])
            ak = (exchange.get_type_code(), row[2])
            exchange_account = ExchangeAccount(row[0], exchange, row[2])
            self.entity_by_id[ExchangeAccount][row[0]] = exchange_account
            self.entity_by_ak[ExchangeAccount][ak] = exchange_account

        self.cur.execute("SELECT exchange_order_id, exchange_id, exchange_instrument_id, order_type_id, "
                         "exchange_account_id, side_id, time_in_force_id, exchange_order_uuid, price,"
                         "quantity, create_time FROM serenity.exchange_order")
        for row in self.cur.fetchall():
            exchange_order_id = row[0]
            exchange = self.type_code_cache.get_by_id(Exchange, row[1])
            exch_instr = self.instrument_cache.get_entity_by_id(ExchangeInstrument, row[2])
            order_type = self.type_code_cache.get_by_id(OrderType, row[3])
            exchange_account = self.entity_by_id[ExchangeAccount][row[4]]
            side = self.type_code_cache.get_by_id(Side, row[5])
            time_in_force = self.type_code_cache.get_by_id(TimeInForce, row[6])
            order_uuid = row[7]
            price = row[8]
            quantity = row[9]
            create_time = row[10]
            ak = (exchange.get_type_code(), order_uuid)

            exchange_order = ExchangeOrder(exchange_order_id, exchange, exch_instr, order_type, exchange_account,
                                           side, time_in_force, order_uuid, price, quantity, create_time)
            self.entity_by_id[ExchangeOrder][exchange_order_id] = exchange_order
            self.entity_by_ak[ExchangeOrder][ak] = exchange_order

    def get_or_create_account(self, account: ExchangeAccount):
        ak = (account.get_exchange().get_type_code(), account.get_exchange_account_num())
        if ak in self.entity_by_ak[ExchangeAccount]:
            return self.entity_by_ak[ExchangeAccount][ak]
        else:
            self.cur.execute("INSERT INTO serenity.exchange_account (exchange_id, exchange_account_num) "
                             "VALUES (%s, %s) RETURNING exchange_account_id", (account.get_exchange().get_type_id(),
                                                                               account.get_exchange_account_num()))
            exchange_account_id = self.cur.fetchone()[0]
            account.set_exchange_account_id(exchange_account_id)
            self.entity_by_id[ExchangeAccount][exchange_account_id] = account
            self.entity_by_ak[ExchangeAccount][ak] = account
            return account

    def get_or_create_exchange_order(self, order: ExchangeOrder):
        ak = (order.get_exchange().get_type_code(), order.get_exchange_order_uuid())
        if ak in self.entity_by_ak[ExchangeOrder]:
            return self.entity_by_ak[ExchangeOrder][ak]
        else:
            self.cur.execute("INSERT INTO serenity.exchange_order (exchange_id, exchange_instrument_id, order_type_id, "
                             "exchange_account_id, side_id, time_in_force_id, exchange_order_uuid, price, quantity, "
                             "create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING exchange_order_id",
                             (order.get_exchange().get_type_id(), order.get_instrument().get_exchange_instrument_id(),
                              order.get_order_type().get_type_id(),
                              order.get_exchange_account().get_exchange_account_id(),
                              order.get_side().get_type_id(), order.get_time_in_force().get_type_id(),
                              order.get_exchange_order_uuid(), order.get_price(), order.get_quantity(),
                              order.get_create_time()))
            exchange_order_id = self.cur.fetchone()[0]
            order.set_exchange_order_id(exchange_order_id)
            self.entity_by_id[ExchangeOrder][exchange_order_id] = order
            self.entity_by_ak[ExchangeOrder][ak] = order
            return order

    def create_exchange_fill(self, fill: ExchangeFill):
        self.cur.execute("INSERT INTO serenity.exchange_fill (exchange_order_id, fill_price, quantity,"
                         "fees, trade_id, create_time) VALUES (%s, %s, %s, %s, %s, %s)",
                         (fill.get_order().get_exchange_order_id(), fill.get_fill_price(), fill.get_quantity(),
                          fill.get_fees(), fill.get_trade_id(), fill.get_create_time()))

    def get_entity_by_ak(self, klass, ak):
        return self.entity_by_ak[klass][ak]


def backfill_coinbasepro(api_key: str, api_secret: str, api_passphrase: str):
    conn = connect_serenity_db()
    cur = conn.cursor()
    type_code_cache = TypeCodeCache(cur)
    instrument_cache = InstrumentCache(cur, type_code_cache)
    exch_service = ExchangeService(cur, type_code_cache, instrument_cache)
    auth_client = coinbasepro.AuthenticatedClient(key=api_key, secret=api_secret, passphrase=api_passphrase)

    # Coinbase Pro has a notion of account per currency for tracking balances, so we want to pull
    # out what it calls the profile, which is the parent exchange account
    profile_set = set()
    for account in auth_client.get_accounts():
        profile_set.add(account['profile_id'])

    exchange = type_code_cache.get_by_code(Exchange, "CoinbasePro")
    account_by_profile_id = {}
    for profile in profile_set:
        account = exch_service.get_or_create_account(ExchangeAccount(0, exchange, profile))
        account_by_profile_id[profile] = account

    # load up all the orders
    for order in auth_client.get_orders(status=['done']):
        order_uuid = order['id']

        # market orders have no price
        if 'price' in order:
            price = order['price']
        else:
            price = None

        # market orders that specify "funds" have no size
        if 'size' in order:
            size = order['size']
        else:
            size = order['filled_size']

        exchange_account = account_by_profile_id[order['profile_id']]
        instrument_type = type_code_cache.get_by_code(InstrumentType, 'CurrencyPair')
        instrument = instrument_cache.get_or_create_instrument(order['product_id'], instrument_type)
        exchange_instrument = instrument_cache.get_or_create_exchange_instrument(order['product_id'], instrument,
                                                                                 exchange.get_type_code())
        side = type_code_cache.get_by_code(Side, order['side'].capitalize())

        if order['type'] is None:
            order['type'] = 'Market'

        order_type = type_code_cache.get_by_code(OrderType, order['type'].capitalize())
        if 'time_in_force' in order:
            tif = type_code_cache.get_by_code(TimeInForce, order['time_in_force'])
        else:
            tif = type_code_cache.get_by_code(TimeInForce, 'Day')
        create_time = order['created_at']

        order = ExchangeOrder(0, exchange, exchange_instrument, order_type, exchange_account,
                              side, tif, order_uuid, price, size, create_time)
        exch_service.get_or_create_exchange_order(order)

    conn.commit()

    # load up all the fills, linking back to the orders
    for fill in auth_client.get_fills(product_id='BTC-USD'):
        order_id = fill['order_id']
        trade_id = fill['trade_id']
        price = fill['price']
        size = fill['size']
        fees = fill['fee']
        create_time = fill['created_at']

        order = exch_service.get_entity_by_ak(ExchangeOrder, (exchange.get_type_code(), order_id))
        fill = ExchangeFill(0, price, size, fees, trade_id, create_time)
        fill.set_order(order)
        exch_service.create_exchange_fill(fill)

    conn.commit()


if __name__ == '__main__':
    fire.Fire(backfill_coinbasepro)
