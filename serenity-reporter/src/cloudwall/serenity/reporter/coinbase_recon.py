import coinbasepro
import fire


def reconcile_coinbasepro(api_key: str, api_secret: str, api_passphrase: str):
    auth_client = coinbasepro.AuthenticatedClient(key=api_key, secret=api_secret, passphrase=api_passphrase)
    print(auth_client.get_accounts())

    for fill in auth_client.get_fills(product_id='BTC-USD'):
        print(fill)

    for order in auth_client.get_orders(status=['done']):
        print(order)


if __name__ == '__main__':
    fire.Fire(reconcile_coinbasepro)



