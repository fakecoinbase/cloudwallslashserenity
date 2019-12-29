from datetime import datetime
from decimal import Decimal

from cloudwall.serenity.model import TypeCode
from cloudwall.serenity.model.instrument import Instrument, Currency


class Exchange(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class ExchangeInstrument:
    def __init__(self, exchange_instrument_id: int, exchange: Exchange, instrument: Instrument,
                 exchange_instrument_code: str):
        self.exchange_instrument_id = exchange_instrument_id

        self.exchange = exchange
        self.instrument = instrument

        self.exchange_instrument_code = exchange_instrument_code

    def get_exchange(self) -> Exchange:
        return self.exchange

    def get_instrument(self) -> Instrument:
        return self.instrument

    def get_exchange_instrument_id(self) -> int:
        return self.exchange_instrument_id

    def get_exchange_instrument_code(self) -> str:
        return self.exchange_instrument_code


class ExchangeAccount:
    def __init__(self, exchange_account_id: int, exchange_account_num: str, exchange: Exchange):
        self.exchange_account_id = exchange_account_id

        self.exchange = exchange

        self.exchange_accont_num = exchange_account_num

    def get_exchange_account_id(self) -> int:
        return self.exchange_account_id

    def get_exchange(self) -> Exchange:
        return self.exchange

    def get_exchange_account_num(self) -> str:
        return self.exchange_accont_num


class ExchangeTransferMethod(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class ExchangeTransferType(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class ExchangeTransferDestinationType(TypeCode):
    def __init__(self, type_id: int, type_code: str):
        super().__init__(type_id, type_code)


class ExchangeTransferDestination:
    def __init__(self, exchange_transfer_destination_id: int,
                 exchange_transfer_destination_type: ExchangeTransferDestinationType,
                 destination_name: str, destination_address: str):
        self.exchange_transfer_destination_id = exchange_transfer_destination_id

        self.exchange_transfer_destination_type = exchange_transfer_destination_type

        self.destination_name = destination_name
        self.destination_address = destination_address

    def get_exchange_transfer_destination_id(self) -> int:
        return self.exchange_transfer_destination_id

    def get_exchange_transfer_destination_type(self) -> ExchangeTransferDestinationType:
        return self.exchange_transfer_destination_type

    def get_destination_name(self) -> str:
        return self.destination_name

    def get_destination_address(self) -> str:
        return self.destination_address


class ExchangeTransfer:
    def __init__(self, exchange_transfer_id: int, exchange_transfer_type: ExchangeTransferType,
                 exchange_transfer_destination: ExchangeTransferDestination,
                 exchange_transfer_method: ExchangeTransferMethod, currency: Currency, quantity: Decimal,
                 transfer_ref: str, transfer_time: datetime):
        self.exchange_transfer_id = exchange_transfer_id

        self.exchange_transfer_type = exchange_transfer_type
        self.exchange_transfer_destination = exchange_transfer_destination
        self.exchange_transfer_method = exchange_transfer_method
        self.currency = currency

        self.quantity = quantity
        self.transfer_ref = transfer_ref
        self.transfer_time = transfer_time

    def get_exchange_transfer_id(self) -> int:
        return self.exchange_transfer_id

    def get_exchange_transfer_type(self) -> ExchangeTransferType:
        return self.exchange_transfer_type

    def get_exchange_transfer_destination(self) -> ExchangeTransferDestination:
        return self.exchange_transfer_destination

    def get_exchange_transfer_method(self) -> ExchangeTransferMethod:
        return self.exchange_transfer_method

    def get_quantity(self) -> Decimal:
        return self.quantity

    def get_transfer_ref(self) -> str:
        return self.transfer_ref

    def get_transfer_time(self) -> datetime:
        return self.transfer_time
